let mongoose = require('mongoose');
let Schema = mongoose.Schema;

let userSchema = new Schema({
    email: {type: String, lowercase: true, unique: true, required: true},
    password: String,
    salt: String,
    SID: String
});

module.exports = mongoose.model('user', userSchema);