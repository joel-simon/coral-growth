class CoralAnimationViewer {
    constructor(verts, colors, faces, vert_indices, face_indices, polyp_geo) {
        console.assert(vert_indices.length == face_indices.length)
        console.assert(verts.length == colors.length)
        this.verts = verts;
        this.colors = colors;
        this.faces = faces;
        this.vert_indices = vert_indices;
        this.face_indices = face_indices;
        this.polyp_geo = polyp_geo;

        this.frame = 0
        this.num_frames = face_indices.length -1 //Drop last frame because it has weird results.
        this.dynamicMesh = new DynamicMesh(MAX_POINTS)
        // this.instanceMesh = new DynamicInstancesMesh(MAX_POINTS, polyp_geo)
        this.dynamicMesh.coral = this
        // this.instanceMesh.coral = this
        this.setFrame(0)
    }
    addToScene(scene) {
        scene.add(this.dynamicMesh.mesh)
        // scene.add(this.instanceMesh.mesh)
    }
    setPosition(x, y, z) {
        this.dynamicMesh.mesh.position.set(x, y, z);
        // this.instanceMesh.mesh.position.set(x, y, z);
    }
    getPosition() {
        return this.dynamicMesh.mesh.position;
    }
    setRotation(x, y, z) {
        this.dynamicMesh.mesh.rotation.set(x, y, z);
        // this.instanceMesh.mesh.rotation.set(x, y, z);
    }
    setScale(scale) {
        this.dynamicMesh.mesh.scale.set(scale, scale, scale);
        // this.instanceMesh.mesh.scale.set(scale, scale, scale);
    }
    setFrame(frame) {
        if (frame >= this.num_frames || frame < 0) {
            throw('Invalid frame', frame)
        }
        this.frame = frame;
        var vert_end = this.vert_indices[this.frame];
        var face_end = this.face_indices[this.frame];
        var vert_start = (this.frame > 0 ? this.vert_indices[this.frame-1] : 0);
        var face_start = (this.frame > 0 ? this.face_indices[this.frame-1] : 0);
        var verts = this.verts.subarray(vert_start, vert_end);
        var colors = this.colors.subarray(vert_start, vert_end);
        var faces = this.faces.subarray(face_start, face_end);

        this.dynamicMesh.update(verts, colors, faces);
        // var directions = this.dynamicMesh.geometry.attributes.normal.array;
        // this.instanceMesh.update(verts, colors, directions);
    }
    nextFrame(reset_on_finish) {
        if (reset_on_finish) {
            this.setFrame((this.frame+1)%this.num_frames)
        } else if (this.frame+1 < this.num_frames) {
            this.setFrame(this.frame+1)
        }
    }

    static fromUrl(path, x=0, z=0, ry = 0) {
        return new Promise((resolve, reject) => {
            console.time('load_coral:'+path)
            const promises = [
                fetch_array(path+'vert_array', Float32Array),
                fetch_array(path+'color_array', Float32Array),
                fetch_array(path+'face_array', Uint32Array),
                fetch_array(path+'vert_indices', Uint32Array),
                fetch_array(path+'face_indices', Uint32Array),
                new Promise((resolve, reject) => {
                    loader.load( 'obj/polyp2.js', resolve, null, reject)
                })
            ]
            Promise.all(promises).then((values) => {
                console.timeEnd('load_coral:'+path)
                const coral = new CoralAnimationViewer(values[0],values[1], values[2],
                                                 values[3], values[4], values[5])
                coral.setPosition(x, 0, z)
                coral.setRotation(0, ry, 0)
                coral.addToScene(scene)
                resolve(coral)
            }).catch(reject)
        })
    }
}

function load_coral(url, x, z, ry) {
    return CoralAnimationViewer.fromUrl(url, x, z, ry)
}
