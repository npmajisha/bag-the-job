/**
 * Created by akhil on 11/21/15.
 */
var express = require('express');
var app = express();
var solr = require('solr-client');
var router = express.Router();
var bodyParser = require('body-parser');
var async = require('async');
var env = process.env.ENV;
var config = require('../config.json');

app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({extended: true})); // support encoded bodies

/* GET course listing. */
router.get('/', function (req, res, next) {

    var keywords = req.query.keywords;

    // get course listings for each keyword in parallel
    async.map(keywords, getCourseListing,
        function (error, results) {
            res.send(results);
        });
});

// callback to get listings for a keyword
function getCourseListing(keyword, callback) {
    var client = solr.createClient(host = config[env].ec2InstanceIP,
        port = config[env].ec2InstancePORT,
        core = config[env].solrCoreCourses);

    var query = client.createQuery()
        .q(keyword)
        .start(0)
        .rows(10);
    client.search(query, function (error, response) {
        callback(error, response);
    });
}

module.exports = router;