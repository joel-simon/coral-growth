
var express = require('express'),
    app = require('express')(),
    server = require('http').createServer(app),
    io = require('socket.io').listen(server),
    fs = require('fs')
    path = require('path');

app.use(express.static('public'))

app.get('/haeckel', function (req, res) {
    res.sendFile(__dirname + '/public/haeckel.html');
});

app.get('/animate_growth', function (req, res) {
    res.sendFile(__dirname + '/public/animate_growth.html');
});


app.get('/', function (req, res) {
    res.sendFile(__dirname + '/public/reef_party.html');
});

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


server.listen(9001);
