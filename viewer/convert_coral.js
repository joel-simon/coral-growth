'use strict'
var glob = require("glob")
var path = require('path');
var fs = require('fs');
var convert = require('color-convert');
var PCA = require('ml-pca');
var math = require('mathjs')

var polyp_data = []
var coral_data = {}
var view_names = null
var n_views = null

var vert_indices = []
var face_indices = []
var radii = []
var verts = []
var colors = []
var faces = []
var values = [];

function save_array(file_name, array) {
    fs.writeFileSync(file_name, new Buffer(array.buffer))
}

function clamp(num, min, max) {
  return num <= min ? min : num >= max ? max : num;
}

function parse_and_add_file(path) {
    var array = fs.readFileSync(path).toString().split("\n");
    var header = null
    var r, g, b, rgb, type;

    var n_color_values = 5; // [ mu_0 mu_1 sig_0 sig_1 sig_2 ]

    for (i in array) {
        split = array[i].split(' ')
        type = split[0]

        switch(type) {
            case '#coral':
                header = split
                break;
            case '#attr':
                break;
            case 'c':
                values.push([ parseFloat(split[1]),
                              parseFloat(split[2]),
                              parseFloat(split[3]),
                              parseFloat(split[4]),
                              parseFloat(split[5]) ]);

                // r = clamp(parseFloat(split[1]), 0, 1);
                // g = clamp(parseFloat(split[2]), 0, 1);
                // b = clamp(parseFloat(split[3]), 0, 1);
                // colors.push(r);
                // colors.push(g);
                // colors.push(b);
                break

            case 'v':
                verts.push(parseFloat(split[1]))
                verts.push(parseFloat(split[2]))
                verts.push(parseFloat(split[3]))
                break

            case 'f':
                faces.push(parseInt(split[1])-1)
                faces.push(parseInt(split[2])-1)
                faces.push(parseInt(split[3])-1)
                break
        }
    }
    vert_indices.push(verts.length)
    face_indices.push(faces.length)
}

function process_files(files) {
    console.log(files.length, 'files found.');
    if (files.length == 0) {
        return
        // process.exit(1);
    }
    // Drop the last file.
    for (i in files) {
        parse_and_add_file(files[i])
    }

    var matrix_t = math.transpose(math.matrix(values))
    var pca = new PCA(values);
    var variances = pca.getExplainedVariance();

    console.log(variances, variances[0]+variances[1]+variances[2]);

    var pca_values = pca.predict(values);
    var mins = math.min(pca_values, 0);
    var maxs = math.max(pca_values, 0);

    var scales = math.subtract(maxs, mins);

    pca_values.forEach((value, index, matrix) => {
        //red
        colors.push((value[1] - mins[1]) / scales[1]);

        //green
        colors.push((value[2] - mins[2]) / scales[2]);

        //blue
        colors.push((value[0] - mins[0]) / scales[0]);
    });

    /*
        Convert to arrays and save.
    */
    var vert_array = Float32Array.from(verts);
    var color_array = Float32Array.from(colors);
    var face_array = Uint32Array.from(faces);

    var last_vi = vert_indices[vert_indices.length-2];
    var last_fi = face_indices[face_indices.length-2];

    save_array(path.join(out_dir, 'last_vert_array'), vert_array.slice(last_vi, vert_array.length));
    save_array(path.join(out_dir, 'last_color_array'), color_array.slice(last_vi, color_array.length));
    save_array(path.join(out_dir, 'last_face_array'), face_array.slice(last_fi, face_array.length));

    save_array(path.join(out_dir,'vert_array'), vert_array);
    save_array(path.join(out_dir,'color_array'), color_array);
    save_array(path.join(out_dir,'face_array'), face_array);
    save_array(path.join(out_dir,'vert_indices'), Uint32Array.from(vert_indices));
    save_array(path.join(out_dir,'face_indices'), Uint32Array.from(face_indices));
}

// if (process.argv.length != 4) {
//     console.log('Must input name and path to a coral output.');
//     process.exit();
// }

var in_dir = process.argv[2];

var directory_mode = false;
process.argv.forEach(function (val, index, array) {
    if (val == 'd') {
        directory_mode = true;
    }
});
console.log('directory_mode =', directory_mode);
var split = in_dir.split('/');
if (directory_mode) {
    var out_dir = 'public/data/'+split[split.length-2].split('__')[0]+'_evolve'
} else {
    var out_dir = 'public/data/'+split[split.length-3].split('__')[0] + '_g'+split[split.length-2];
}

console.log(out_dir);

if (!fs.existsSync(out_dir)){
    fs.mkdirSync(out_dir);
}

function getDirectories(path) {
    return fs.readdirSync(path).filter(function (file) {
        return fs.statSync(path+'/'+file).isDirectory();
    });
}

function sort_coral_objs(files){
    files.sort(function(a, b) {
        var i = parseInt(a.match(/(\d+).coral.obj/)[1]);
        var j = parseInt(b.match(/(\d+).coral.obj/)[1]);
        return i-j;
    });
}

if (directory_mode) {
    var pattern, files;
    var evolve_files = [ ];
    var directories = getDirectories(in_dir);
    directories.sort((a, b) => parseInt(a) - parseInt(b));

    for (var i = 0; i < directories.length; i++) {
        pattern = path.join(in_dir, directories[i], '0', "*.coral.obj");
        files = glob.sync(pattern);
        sort_coral_objs(files);
        evolve_files.push(files[files.length-2]); //Drop the last file.
    }
    process_files(evolve_files)

} else {
    glob(path.join(in_dir+'0/', "*.coral.obj"), function (er, files) {
        sort_coral_objs(files);
        process_files(files.slice(0, -1));
    });
}
