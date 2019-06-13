const express = require('express')
const app = require('express')()
const server = require('http').createServer(app)
const io = require('socket.io').listen(server)
const fs = require('fs')
const path = require('path')


const root = process.argv[2]
// process.chdir(process.argv[2]);
// const root = './'

function getDirectories(path) {
    return fs.readdirSync(path).filter((file) => {
        return fs.statSync(path+'/'+file).isDirectory()
    })
}


function file_cmp (f1, f2) {
    return parseInt(f2.split('.')[0]) -  parseInt(f1.split('.'))
}

// app.get('/haeckel', function (req, res) {
//     res.sendFile(__dirname + '/public/haeckel.html');
// });

// app.get('/animate_growth', function (req, res) {
//     res.sendFile(__dirname + '/public/animate_growth.html');
// });

app.get('/', (req, res) => {
    const html = getDirectories(root).map(name => {
        return `<a href=/dir/${name}>${name}</a><br>`
    }).join('')
    res.set('Content-Type', 'text/html')
    res.send(new Buffer.from(html))
})

app.get('/dir/:dir', (req, res) => {
    const { dir } = req.params
    const html = getDirectories(`${root}/${dir}`).sort(file_cmp).map(name => {
        return `<a href=/view/${dir}/${name}/>${name}</a><br>`
    }).join('')
    res.set('Content-Type', 'text/html')
    res.send(new Buffer.from(html))
})

app.get('/view/:dir/:gen', (req, res) => {
    const { dir, gen } = req.params
    const obj_dir = `${root}/${dir}/${gen}/0/`
    const paths = fs.readdirSync(obj_dir).filter((f) => f.endsWith('.obj'))
    const max_path = paths.sort(file_cmp)[0]
    res.redirect('/viewer?obj='+encodeURIComponent(`${dir}/${gen}/0/${max_path}`))
})

app.get('/obj/:path', (req, res) => {
    // For loading the 3d objects.
    const full_path = path.resolve(path.join(root, decodeURIComponent(req.params.path)))
    console.log(full_path)
    // console.log()
    res.sendFile(full_path)
})

app.get('/viewer', (req, res) => {
    return res.sendFile(__dirname + '/public/obj_viewer.html')
})

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
