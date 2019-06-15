const fs = require('fs')
const convert_utils = require('./convert_utils.js')

const in_dir = process.argv[2]
const out_dir = process.argv[3]

function main(in_dir, out_dir) {
    if (!fs.existsSync(out_dir)) {
        fs.mkdirSync(out_dir)
    }
    const obj_paths = convert_utils.get_obj_paths(in_dir)
    const data = convert_utils.read_and_color(obj_paths)
    convert_utils.write_objs(out_dir, data)
}

main(in_dir, out_dir)