const fs = require('fs')
const assert = require('assert')
const PCA = require('ml-pca')
const math = require('mathjs')
const path = require('path')

const concat = (arrays) => [].concat.apply([], arrays)
function clamp(num, min, max) {
    return num <= min ? min : num >= max ? max : num;
}

module.exports = {
    save_array(file_name, array) {
        fs.writeFileSync(file_name, new Buffer(array.buffer))
    },
    parse_obj(path) {
        const data = []
        const verts = []
        const faces = []
        const array = fs.readFileSync(path).toString().split("\n")
        const header = array[1].split(' ')
        assert(array[0] == '#Exported from growth_forms')
        assert(header[0] == '#form')
        const to_use = []
        header.slice(1).forEach((name, idx) => {
            if (name.startsWith('mem_') ||
                name.startsWith('sig_') ||
                name.startsWith('mu_'))
            {
                to_use.push(idx)
            }
        })
        for (i in array) {
            const split = array[i].split(' ')
            const type = split[0]
            switch(type) {
                case 'c': // Custom data stored here.
                    data.push(to_use.map(idx => parseFloat(split[idx+1])))
                    break
                case 'v':
                    verts.push([
                        parseFloat(split[1]),
                        parseFloat(split[2]),
                        parseFloat(split[3])
                    ])
                    // verts.push()
                    // verts.push(parseFloat(split[2]))
                    // verts.push(parseFloat(split[3]))
                    break
                case 'f':
                    faces.push([
                        parseInt(split[1])-1,
                        parseInt(split[2])-1,
                        parseInt(split[3])-1
                    ])
                    // faces.push()
                    // faces.push(parseInt(split[2])-1)
                    // faces.push(parseInt(split[3])-1)
                    break
            }
        }
        return { data, verts, faces }
    },
    read_and_color(files) {
        const parsed_files = []
        for (const file of files) {
            const obj_data = this.parse_obj(file)
            parsed_files.push(obj_data)
        }
        const pca = new PCA(concat(parsed_files.map(f => f.data)))
        const variances = pca.getExplainedVariance()
        console.log(variances, variances[0]+variances[1]+variances[2])

        for (const obj_data of parsed_files) {
            const pca_data = pca.predict(obj_data.data)
            const mins = math.min(pca_data, 0)
            const maxs = math.max(pca_data, 0)
            const scales = math.subtract(maxs, mins)
            obj_data.colors = []
            pca_data.forEach((value, index) => {
                obj_data.colors.push([
                    (value[1] - mins[1]) / scales[1], // red
                    (value[2] - mins[2]) / scales[2], // green
                    (value[0] - mins[0]) / scales[0] // blue
                ])
                // obj_data.colors.push((value[1] - mins[1]) / scales[1]) //red
                // obj_data.colors.push((value[2] - mins[2]) / scales[2]) //green
                // obj_data.colors.push((value[0] - mins[0]) / scales[0]) //blue
            })
        }
        return parsed_files
    },
    write_objs(out_dir, data) {
        data.forEach(({ colors, verts, faces }, idx) => {
            // console.log(verts, verts.forEach)
            const rows = []
            verts.forEach((p, vid) => {
                const [x, y, z] = p
                const [r, g, b] = colors[vid]
                rows.push(`v ${x} ${y} ${z} ${r} ${g} ${b}`)
            })
            for (const face of faces) {
                rows.push('f '+face.map(i => i+1).join(' '))
            }
            obj_string = rows.join('\n')
            fs.writeFileSync(path.join(out_dir, idx.toString().padStart(4))+'.obj', obj_string)
        })
    },
    sort_coral_names(names) {
        names.sort((a, b) => {
            const i = parseInt(a.match(/(\d+).form.obj/)[1])
            const j = parseInt(b.match(/(\d+).form.obj/)[1])
            return i-j;
        })
    },
    get_obj_paths(dir) {
        const names = fs.readdirSync(dir).filter((f) => f.endsWith('.obj'))
        this.sort_coral_names(names)
        return names.map(name => path.join(dir, name))
    }
}
