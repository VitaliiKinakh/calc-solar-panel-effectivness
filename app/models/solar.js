let mongoose = require('mongoose');
let autoIncrement = require('../../remastered_modules/mongoose-auto-increment.js');
let Schema = mongoose.Schema;

let solarSchema = new Schema({
    id: {type: Number, index:true, unique: true },
    email: {type: String, lowercase: true, unique: true, required: true},
    location: {x: Number, y: Number},
    area: Number,
    efe: Number
});

autoIncrement.initialize(mongoose.connection);
solarSchema.plugin(autoIncrement.plugin, { model: 'solar', field: 'id', startAt: 1 });
module.exports = mongoose.model('solar', solarSchema);