const glob = require("glob")
const path = require('path')
const fs = require('fs')
const utils = require('./convert_utils.js')

function main(in_dir, out_dir) {
    if (!fs.existsSync(out_dir)) { fs.mkdirSync(out_dir) }
    console.time('obj2buffer')
    const obj_paths = utils.get_obj_paths(in_dir)
    const data = utils.read_and_color(obj_paths)
    const buffers = utils.data2buffers(data)
    utils.save_array(path.join(out_dir,'vert_array'), buffers.vert_buffer)
    utils.save_array(path.join(out_dir,'color_array'), buffers.color_buffer)
    utils.save_array(path.join(out_dir,'face_array'), buffers.face_buffer)
    utils.save_array(path.join(out_dir,'vert_indices'), buffers.vert_indices)
    utils.save_array(path.join(out_dir,'face_indices'), buffers.face_indices)
    console.timeEnd('obj2buffer')
}
module.exports = main

if (require.main === module) {
    const in_dir = process.argv[2]
    const out_dir = process.argv[3]
    main(in_dir, out_dir)
}



// var in_dir = process.argv[2];

// var directory_mode = false;
// process.argv.forEach(function (val, index, array) {
//     if (val == 'd') {
//         directory_mode = true;
//     }
// });
// console.log('directory_mode =', directory_mode);
// var split = in_dir.split('/');
// if (directory_mode) {
//     var out_dir = 'public/data/'+split[split.length-2].split('__')[0]+'_evolve'
// } else {
//     var out_dir = 'public/data/'+split[split.length-3].split('__')[0] + '_g'+split[split.length-2];
// }

// console.log(out_dir);

// if (!fs.existsSync(out_dir)){
//     fs.mkdirSync(out_dir);
// }

// function getDirectories(path) {
//     return fs.readdirSync(path).filter(function (file) {
//         return fs.statSync(path+'/'+file).isDirectory();
//     });
// }

// function sort_coral_objs(files){
//     files.sort(function(a, b) {
//         var i = parseInt(a.match(/(\d+).coral.obj/)[1]);
//         var j = parseInt(b.match(/(\d+).coral.obj/)[1]);
//         return i-j;
//     });
// }

// if (directory_mode) {
//     var pattern, files;
//     var evolve_files = [ ];
//     var directories = getDirectories(in_dir);
//     directories.sort((a, b) => parseInt(a) - parseInt(b));

//     for (var i = 0; i < directories.length; i++) {
//         pattern = path.join(in_dir, directories[i], '0', "*.coral.obj");
//         files = glob.sync(pattern);
//         sort_coral_objs(files);
//         evolve_files.push(files[files.length-2]); //Drop the last file.
//     }
//     process_files(evolve_files)

// } else {
//     glob(path.join(in_dir+'0/', "*.coral.obj"), function (er, files) {
//         sort_coral_objs(files);
//         process_files(files.slice(0, -1));
//     });
// }


