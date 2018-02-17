let express = require('express');
let path = require('path');
let bodyParser = require('body-parser');
let morgan = require('morgan');
let helmet = require('helmet');
let mongoose = require('mongoose');
let cors = require('cors');
let autoParse = require('auto-parse');

let app = express();

let port = process.env.PORT || 42303;

app.use(cors());
app.use(helmet());
app.use(morgan('tiny'));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "public")));

//CONNECTING TO DATABASE
mongoose.Promise = global.Promise;
let options = {
    //useMongoClient: true,
    reconnectTries: Number.MAX_VALUE,
    reconnectInterval: 100,
    poolSize: 10,
    bufferMaxEntries: 0
};
let uri = process.env.MONGODB_URI || 'mongodb://localhost:27015/suncalc';
mongoose.connect(uri, options);

// REGISTER ROUTES -------------------------------
let solarAPI = require('./app/routes/solarAPI');
let users = require('./app/routes/users');
let solars = require('./app/routes/solars')

//Check if request is valid and parse numbers represented as string etc
app.use(function (err, req, res, next) {
    if(err) res.status(400).send('Bad request body');
    else next();
});
app.all('/*', function(req, res, next) {
    if(Object.keys(req.body).length !== 0){
        req.body = autoParse(req.body);
    }
    if(Object.keys(req.query).length !== 0){
        req.query = autoParse(req.query);
    }
    next();
});

app.get('/', function(req, res) {
    res.sendFile(path.join(__dirname, 'public', 'pages', 'index.html'));
});

//Log if error
function modifyResponseBody(req, res, next) {
    let oldSend = res.send;
    res.send = function(data){
        if(typeof autoParse(data) === 'string' && data!=='OK'){
            let ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress || req.socket.remoteAddress || req.connection.socket.remoteAddress;
            console.log('REQUEST FROM IP ( ' +ip+ ' ):');
            if(Object.keys(req.body).length !== 0){
                console.log(req.body);
            }
            if(Object.keys(req.query).length !== 0){
                console.log(req.query);
            }
            console.log();
            console.log('RESPONSE:');
            console.log(data);
            console.log();
        }
        res.send=oldSend;
        oldSend.apply(res, arguments);
    };
    next();
}
app.use(modifyResponseBody);

app.use('/api/solarAPI', solarAPI);
app.use('/api/solars', solars);
app.use('/api/users', users);
// START THE SERVER -------------------------------
const server = app.listen(port);
server.timeout = 3600000;
console.log('Server started on port ' + port);