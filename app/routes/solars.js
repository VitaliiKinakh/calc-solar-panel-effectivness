let express = require('express');
let crypto = require('crypto');
let router = express.Router();
let validator = require("email-validator");
let userModel = require('../models/user.js');
let solarModel = require('../models/solar.js')

router.route('/')
    .get(function (req, res) {
        let SID = req.query.SID;
        userModel.findOne({'SID': SID}, 'email -_id', function (err, user) {
            if(err) res.status(400).send("Can't find you in our user lists");
            else if(user){
                solarModel.find({'email': user.email}, '-_id -__v', function (err, panels) {
                    if(err) res.status(400).send("There was error finding your panels");
                    else res.json(panels);
                })
            }else res.status(400).send('Are you logged in?');
        });
    })
    .post(function (req, res) {
        let SID = req.body.SID;
        let location = req.body.location;
        let area = req.body.area;
        let efe = req.body.efe;
        userModel.findOne({'SID': SID}, 'email -_id', function (err, user) {
            if(err) res.status(400).send("Can't find you in our user lists");
            else if(user){
                if(location&&location.x!==undefined&&location.y!==undefined) {
                    if(area!==undefined&&area>0){
                        if(efe!==undefined&&efe>0&&efe<1){
                            let newSolar = new solarModel({email:user.email, location:{x:location.x, y:location.y}, area: area, efe:efe});
                            newSolar.save(function (err) {
                                if(err) res.status(400).send("Can't save your solar panel right now");
                                else res.sendStatus(200);
                            })
                        }else res.status(400).send('Please specify valid efficieny');
                    }else res.status(400).send('Please specify valid area');
                }else res.status(400).send('Please specify right coordinates');
            }else res.status(400).send('Are you logged in?');
        });
    });

module.exports = router;