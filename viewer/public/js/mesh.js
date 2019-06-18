class DynamicInstancesMesh {
    constructor(instanceCount, geo) {
        // this.position.
        this.materialList = [];
        this.geometryList = [];
        var vert = document.getElementById( 'vertInstanced' ).textContent;
        var frag = document.getElementById( 'fragInstanced' ).textContent;

        var material = new THREE.RawShaderMaterial( {
            vertexShader: vert,
            fragmentShader: frag,
        } );

        this.materialList.push( material );

        var bgeo = new THREE.BufferGeometry().fromGeometry( geo );
        this.geometryList.push( bgeo );

        this.igeo = new THREE.InstancedBufferGeometry();
        this.igeo.maxInstancedCount = 0;
        this.geometryList.push( this.igeo );

        var vertices = bgeo.attributes.position.clone();
        this.igeo.addAttribute( 'position', vertices );

        var mcol0 = new THREE.InstancedBufferAttribute(
            new Float32Array( instanceCount * 3 ), 3, 1
        );
        var mcol1 = new THREE.InstancedBufferAttribute(
            new Float32Array( instanceCount * 3 ), 3, 1
        );
        var mcol2 = new THREE.InstancedBufferAttribute(
            new Float32Array( instanceCount * 3 ), 3, 1
        );
        var mcol3 = new THREE.InstancedBufferAttribute(
            new Float32Array( instanceCount * 3 ), 3, 1
        );
        var colors = new THREE.InstancedBufferAttribute(
            new Float32Array( instanceCount * 3 ), 3, 1
        );
        this.igeo.addAttribute( 'mcol0', mcol0 );
        this.igeo.addAttribute( 'mcol1', mcol1 );
        this.igeo.addAttribute( 'mcol2', mcol2 );
        this.igeo.addAttribute( 'mcol3', mcol3 );
        this.igeo.addAttribute( 'color', colors );
        this.mesh = new THREE.Mesh( this.igeo, material );
    }

    update(positions, colors, directions) {
        var matrix = new THREE.Matrix4();
        var me = matrix.elements;

        var position = new THREE.Vector3();
        var rotation = new THREE.Euler();
        var quaternion = new THREE.Quaternion();
        var scale = new THREE.Vector3();

        var mcol0 = this.igeo.attributes.mcol0
        var mcol1 = this.igeo.attributes.mcol1
        var mcol2 = this.igeo.attributes.mcol2
        var mcol3 = this.igeo.attributes.mcol3
        var color = this.igeo.attributes.color

        var up = new THREE.Vector3( 0, 1, 0 );
        var vec = new THREE.Vector3(0, 0, 0)

        for ( var i = 0; i < positions.length/3; i ++ ) {
            position.x = positions[3*i];
            position.y = positions[3*i+1];
            position.z = positions[3*i+2];

            vec.x = directions[3*i];
            vec.y = directions[3*i+1];
            vec.z = directions[3*i+2];

            quaternion.setFromUnitVectors( up, vec );
            scale.x = scale.y = scale.z = .010;

            matrix.compose( position, quaternion, scale );
            mcol0.setXYZ( i, me[ 0 ], me[ 1 ], me[ 2 ] );
            mcol1.setXYZ( i, me[ 4 ], me[ 5 ], me[ 6 ] );
            mcol2.setXYZ( i, me[ 8 ], me[ 9 ], me[ 10 ] );
            mcol3.setXYZ( i, me[ 12 ], me[ 13 ], me[ 14 ] );
            color.setXYZ( i, colors[3*i], colors[3*i+1], colors[3*i+2]);
        }

        // mesh
        this.igeo.maxInstancedCount = positions.length/3;
        mcol0.needsUpdate = true;
        mcol1.needsUpdate = true;
        mcol2.needsUpdate = true;
        mcol3.needsUpdate = true;
        color.needsUpdate = true;
        this.igeo.computeVertexNormals();
        this.igeo.computeBoundingSphere();
    }
}

class DynamicMesh {
    constructor(max_verts) {
        this.max_verts = max_verts
        this.geometry = new THREE.BufferGeometry()
        var positions = new Float32Array( max_verts * 3 );
        var colors = new Float32Array( max_verts * 3 );
        var indexes = new Uint32Array( max_verts * 6 );
        this.geometry.addAttribute( 'position', new THREE.BufferAttribute( positions, 3 ));
        this.geometry.addAttribute( 'color', new THREE.BufferAttribute( colors, 3 ));
        this.geometry.setIndex(new THREE.BufferAttribute( indexes, 1 ));

        var material = new THREE.MeshPhongMaterial( {
            shininess: 100,
            // flatShading: true,
            vertexColors: THREE.VertexColors,
        } );

        this.mesh = new THREE.Mesh( this.geometry, material );
        this.mesh.castShadow = true;
        this.mesh.receiveShadow = true;
    }

    update(position, color, indices) {
        if (position.length > this.max_verts *3) {
            throw 'Position array too long', [position.length, this.max_verts]
        }
        this.geometry.attributes.position.array.fill(0);
        this.geometry.attributes.position.array.set(position);
        this.geometry.attributes.color.array.set(color);
        this.geometry.index.array.set(indices);
        this.geometry.index.array.fill(0, indices.length);// Fill rest with 0.
        this.geometry.setDrawRange(0, position.length*3);
        this.geometry.attributes.position.needsUpdate = true;
        this.geometry.attributes.color.needsUpdate = true;
        this.geometry.index.needsUpdate = true;
        this.geometry.computeVertexNormals();
        this.geometry.computeBoundingSphere();
    }
}
