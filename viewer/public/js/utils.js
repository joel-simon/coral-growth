
// function load_coral(path, scale, position, rotation) {
//     console.time('load_coral'+path)
//     promises = [
//         array_promise(path+'vert_array', Float32Array),
//         array_promise(path+'color_array', Float32Array),
//         array_promise(path+'face_array', Uint32Array),
//         array_promise(path+'vert_indices', Uint32Array),
//         array_promise(path+'face_indices', Uint32Array),
//         new Promise(function (resolve, reject) {
//             loader.load( 'obj/polyp4.js', resolve, null, reject)
//         })
//     ]
//     Promise.all(promises).then(function(values) {
//         console.timeEnd('load_coral'+path)
//         coral = new CoralAnimationViewer(values[0],values[1], values[2],
//                                         values[3], values[4], values[5])
//         coral.setPosition(position.x, position.y, position.z)
//         coral.setRotation(rotation.x, rotation.y, rotation.z)
//         coral.dynamicMesh.mesh.scale.set(scale, scale, scale)
//         // console.log(coral.dynamicMesh.mesh.scale.set());

//         coral.addToScene(scene)
//         coral.setFrame(coral.num_frames-1)
//         corals.push(coral)
//         // click_objects.push(coral.dynamicMesh.mesh)

//     }).catch(function(err){
//         console.log(err);
//     })
// }



function load_coral(path, x=0, z=0, ry = 0) {
    return new Promise(function (resolve, reject) {
        console.time('load_coral'+path)
        promises = [
            array_promise(path+'vert_array', Float32Array),
            array_promise(path+'color_array', Float32Array),
            array_promise(path+'face_array', Uint32Array),
            array_promise(path+'vert_indices', Uint32Array),
            array_promise(path+'face_indices', Uint32Array),
            new Promise(function (resolve, reject) {
                loader.load( 'obj/polyp4.js', resolve, null, reject)
            })
        ]
        Promise.all(promises).then(function(values) {
            console.timeEnd('load_coral'+path)
            coral = new CoralAnimationViewer(values[0],values[1], values[2],
                                            values[3], values[4], values[5])
            coral.setPosition(x, 0, z)
            coral.setRotation(0, ry, 0)
            coral.addToScene(scene)

            resolve(coral)

        }).catch(reject)
    })
}
/*
    Promise wrapper around XMLHttpRequest
*/
function request_promise(url, method, responseType) {
    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.responseType = responseType
        xhr.timeout = 8000; // time in milliseconds
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                resolve(xhr.response);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}

/*
    Load typed array from URL.
*/
function array_promise(url, arraytype) {
    return new Promise(function (resolve, reject) {
        request_promise(url, 'GET', 'arraybuffer').then(function(response) {
            resolve(new arraytype(response))
        }).catch(reject)
    })
}
