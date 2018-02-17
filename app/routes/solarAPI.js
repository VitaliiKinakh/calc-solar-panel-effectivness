let express = require('express');
let router = express.Router();
let spawn = require("child_process").spawn;

function between(x, min, max) {
    return x >= min && x <= max;
}

function swap(min, max) {
    if(min>max){
        let tmp = min;
        min = max;
        max = tmp;
    }
}

router.get('/irradiance_yearly', function (req, res) {
    let lat = req.query.lat; //-90 to 90
    let lng = req.query.lng; //-180 to 180
    if (lat!==undefined && !isNaN(lat) && between(lat, -90, 90) && lng!==undefined && !isNaN(lng) && between(lng, -180, 180)){
        let pythonProcess = spawn('python',["./app.py", "irradiance_sum_yearly", lat, lng]);
        pythonProcess.stdout.on('data', function (data){
            res.json(JSON.parse((data.toString())));
        });
    }else res.status(400).send("Please specify valid coordinates");
});

router.get('/irradiance_period', function (req, res) {
    if (isNaN(Date.parse(req.query.sDate))===false && isNaN(Date.parse(req.query.eDate))===false)
    {
        let startDate = new Date(req.query.sDate);
        let endDate = new Date(req.query.eDate);
        swap(startDate, endDate);
        let maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 7);
        if(endDate>maxDate) endDate=maxDate;
        if(startDate>maxDate) startDate=maxDate;
        let prepared_startDate = startDate.getFullYear()+'-'+(startDate.getMonth()+1)+'-'+startDate.getDate();
        let prepared_endDate = endDate.getFullYear()+'-'+(endDate.getMonth()+1)+'-'+endDate.getDate();

        let lat = req.query.lat; //-90 to 90
        let lng = req.query.lng; //-180 to 180
        if (lat!==undefined && !isNaN(lat) && between(lat, -90, 90) && lng!==undefined && !isNaN(lng) && between(lng, -180, 180)) {
            let pythonProcess = spawn('python', ["./app.py", "irradiance_sum_some_period", lat, lng, prepared_startDate, prepared_endDate]);
            pythonProcess.stdout.on('data', function (data) {
                res.json(JSON.parse((data.toString())));
            });
        }else res.status(400).send("Please specify valid coordinates");
    }else res.status(400).send("Please specify valid dates")

});

router.get('/irradiance_panel_yearly', function (req, res) {
    let lat = req.query.lat; //-90 to 90
    let lng = req.query.lng; //-180 to 180
    let area = req.query.area; //0 to inf
    let efe = req.query.efe; //0 to 1
    if (lat!==undefined && !isNaN(lat) && between(lat, -90, 90) && lng!==undefined && !isNaN(lng) && between(lng, -180, 180)) {
        if(area && !isNaN(area) && area>0){
            if(efe && !isNaN(efe) && between(efe, 0,1)){
                let pythonProcess = spawn('python', ["./app.py", "irradiance_for_panel_yearly", lat, lng, area, efe]);
                pythonProcess.stdout.on('data', function (data) {
                    res.json(JSON.parse(data.toString()));
                });
            }else res.status(400).send("Please specify vaslid efficiency");
        }else res.status(400).send("Please specify valid area of panels");
    }else res.status(400).send("Please specify valid coordinates");
});

router.get('/forecast_irradiance', function (req, res) {
    let lat = req.query.lat; //-90 to 90
    let lng = req.query.lng; //-180 to 180
    if (lat!==undefined && !isNaN(lat) && between(lat, -90, 90) && lng!==undefined && !isNaN(lng) && between(lng, -180, 180)) {
        let pythonProcess = spawn('python', ["./app.py", "forecast_irradiance", lat, lng]);
        pythonProcess.stdout.on('data', function (data) {
            res.json(JSON.parse((data.toString())));
        });
    }else res.status(400).send("Please specify valid coordinates");
});

module.exports = router;
