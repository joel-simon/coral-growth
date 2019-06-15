const express = require('express')
const app = require('express')()
const server = require('http').createServer(app)
const io = require('socket.io').listen(server)
const fs = require('fs')
const path = require('path')
const utils = require('./convert_utils.js')
const objs2buffers = require('./objs2buffers.js')

const root = process.argv[2]
// process.chdir(process.argv[2]);
// const root = './'

function getDirectories(path) {
    return fs.readdirSync(path).filter((file) => {
        return fs.statSync(path+'/'+file).isDirectory()
    })
}

function getFiles(path) {
    return fs.readdirSync(path).filter((file) => {
        return !fs.statSync(path+'/'+file).isDirectory()
    })
}


function file_cmp (f1, f2) {
    return parseInt(f2.split('.')[0]) -  parseInt(f1.split('.'))
}

// app.get('/haeckel', function (req, res) {
//     res.sendFile(__dirname + '/public/haeckel.html');
// });



app.get('/reef', function (req, res) {
    res.sendFile(__dirname + '/public/reef_party.html');
});

app.get('/', (req, res) => {
    const html = getDirectories(root).map(name => {
        return `<a href=/dir/${name}>${name}</a><br>`
    }).join('')
    res.set('Content-Type', 'text/html')
    res.send(new Buffer.from(html))
})

app.get('/dir/:dir', (req, res) => {
    const dir = decodeURIComponent(req.params.dir)
    const path_dir = path.join(root, dir)

    const directories = getDirectories(path_dir)
    const files = getFiles(path_dir)

    /* Treat directory of objs differently */
    if (directories.length == 0 && files.every(f => f.endsWith('.obj'))) {
        const parent = path.dirname(path_dir)
        const animation_dir = path.join(parent, path.basename(dir)+'_animation')

        if (!fs.existsSync(animation_dir)) {
            objs2buffers(path_dir, animation_dir)
        }
        return res.redirect('/animate?data='+ encodeURIComponent(path.join(parent, path.basename(dir)+'_animation')))

        // const max_path = files.sort(file_cmp)[0]
        // return res.redirect('/viewer?obj='+ encodeURIComponent(path.join(dir, max_path)))
    }

    const html =
        directories
        .sort(file_cmp)
        .map(name => `<a href=/dir/${encodeURIComponent(path.join(dir,name))}/>${name}</a><br>` )
        .join('')
        +
        files
        .sort(file_cmp)
        .map(name => `<a href=/view/${encodeURIComponent(path.join(dir,name))}/>${name}</a><br>` )
        .join('')

    res.set('Content-Type', 'text/html')
    res.send(new Buffer.from(html))
})

app.get('/view/:path', (req, res) => {
    const p = path.resolve(path.join(root, decodeURIComponent(req.params.path)))
    if (p.endsWith('.obj')) {
        res.redirect('/viewer?obj='+req.params.path)
    } else {
        res.sendFile(p)
    }
})

app.get('/data/:path', (req, res) => {
    const p = path.resolve(path.join(root, decodeURIComponent(req.params.path)))
    res.sendFile(p)
})

app.get('/viewer', (req, res) => {
    return res.sendFile(__dirname + '/public/obj_viewer.html')
})

app.get('/animate', function (req, res) {
    return res.sendFile(__dirname + '/public/animate_growth.html')
})


// app.get('/obj/:path', (req, res) => {
//     // For loading the 3d objects.
//     const full_path = path.resolve(path.join(root, decodeURIComponent(req.params.path)))
//     res.sendFile(full_path)
// })



io.sockets.on('connection', function (socket) {
    socket.on('render-frame', function (data) {
        console.log(data.out_dir, data.frame);
        var out_dir = path.join(__dirname, 'tmp', data.out_dir);
        if (!fs.existsSync(out_dir)) {
            fs.mkdirSync(out_dir);
        }
        data.file = data.file.split(',')[1]; // Get rid of the data:image/png;base64 at the beginning of the file data
        var buffer = new Buffer(data.file, 'base64');
        var name = (''+data.frame).padStart(5, "0") +'.png';
        fs.writeFileSync(path.join(out_dir, name), buffer.toString('binary'), 'binary');
    });

    // socket.on('empty_frames', function (data) {
    //     var directory = path.join(__dirname, 'tmp');
    //     fs.readdir(directory, (err, files) => {
    //         if (err) throw err;
    //         for (const file of files) {
    //             fs.unlink(path.join(directory, file), err => {
    //                 if (err) throw err;
    //             });
    //         }
    //     });
    // });
});
app.use(express.static('public'))
server.listen(9001)
