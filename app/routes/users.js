let express = require('express');
let crypto = require('crypto');
let router = express.Router();
let validator = require("email-validator");
let userModel = require('../models/user.js');

router.route('/')
    .post(function (req, res) {
        let email = req.body.email;
        let password = req.body.password;
        let salt = crypto.createHash('sha256').update(email + 'SolarStuff').digest('hex');
        password = crypto.createHash('sha256').update(password + salt).digest('hex');
        if (validator.validate(email)) {
            userModel.findOne({
                'email': email,
                'password': password
            }, function (err, user) {
                if(user){
                    if (user.SID) {
                        res.json({'SID': user.SID});
                    }
                    else {
                        user.SID = crypto.createHash('sha256').update('SolarStuff' + salt + Date.now()).digest('hex');
                        user.save(function (err) {
                            if (err) res.sendStatus(400);
                            else {
                                res.json({'SID': user.SID});
                            }
                        })
                    }
                }else{
                    userModel.count({'email': email}, function(err, count){
                        if(!count){
                            let user = new userModel({
                                email: email,
                                password: password,
                                salt: salt,
                                SID: crypto.createHash('sha256').update('SolarStuff' + salt + Date.now()).digest('hex')
                            });
                            user.save(function (err) {
                                if (err) res.status(400).send('Cant register you know');
                                else res.json({'SID': user.SID})
                            });
                        }else res.status(400).send("Wrong password");
                    })
                }
            });
        } else {
            res.status(400).send('Bad email');
        }
    });

router.route('/register')
    .post(function (req, res) {
        let email = req.body.email;
        let password = req.body.password;
        let fullname = req.body.fullname;
        let salt = crypto.createHash('sha256').update(email + 'WebOne').digest('hex');
        password = crypto.createHash('sha256').update(password + salt).digest('hex');
        if (validator.validate(email)) {
            let user = new userModel({
                email: email,
                password: password,
                salt: salt,
                fullname: fullname,
            });
            user.save(function (err) {
                if (err) res.status(400).send('Cant register you know');
                else res.sendStatus(200);
            })
        } else {
            res.status(400).send('Bad email');
        }
    });

module.exports = router;