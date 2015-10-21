var express = require('express');
var app = express();
var solr = require('solr-client');
var router = express.Router();
var bodyParser = require('body-parser');
var env = (process.argv[2] != null) ? process.argv[2] : 'default';
var config = require('../config.json');

app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({extended: true})); // support encoded bodies

/* GET jobs listing. */
router.get('/', function (req, res, next) {
    var city = req.query.city;
    var state = req.query.state;
    var keywords = req.query.keywords;
    var start = req.query.start;
    var noParameters = req.query.noParam;

    var client = solr.createClient(host = config[env].ec2InstanceIP, port = config[env].ec2InstancePORT, core = config[env].solrCore);

    console.log(city + state + keywords);

    var params = {};
    if (city != null) {
        params['jobCity'] = city;
    }
    if (state != null) {
        params['jobState'] = state;
    }
    if (keywords != null) {
        params['jobTitle'] = keywords;
    }
    if (noParameters != null) {
        params["*"] = "*";
    }

    var query = client.createQuery()
        .q(params)
        .start(start)
        .rows(10);
    console.log(query);
    client.search(query, function (err, response) {
        if (err) {
            throw err;
        } else {
            res.send(response.response);
        }
    });
});

module.exports = router;
