
/*
    Promise wrapper around XMLHttpRequest
*/
function request_promise(url, method, responseType) {
    return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.responseType = responseType
        xhr.timeout = 20000;
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
function fetch_array(url, arraytype) {
    return request_promise(url, 'GET', 'arraybuffer').then((response) => {
        return new arraytype(response)
    })
}

// async function fetch_array(url, arraytype) {
//     const res = await window.fetch(url, {
//         method: 'GET',
//         'Content-Type': 'arraybuffer'
//     })
//     const body = await res.blob()
//     console.log(body)
//     console.log(body.buffer())
//     // console.log(buffer.from(body))
//     console.log(arraytype.from(body))
//             // headers: { 'Content-Type': 'arraybuffer'},
//         // }).then(response => {
//             // return response.arrayBuffer().then(data => {
//             //     console.log(data)
//             //     return new arraytype(response.arrayBuffer())
//             // })
//         // })
//         // return request_promise(url, 'GET', 'arraybuffer').then((response) => {
//         // resolve(new arraytype(response))
// //     })
// }