/**
 * Created by akhil on 10/21/15.
 */
var express = require('express');
var app = express();
var router = express.Router();
var bodyParser = require('body-parser');
var books = require('google-books-search');
var async = require('async');

app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({extended: true})); // support encoded bodies

/* GET books listing. */
router.get('/', function (req, res, next) {

    var keywords = req.query.keywords;

    // get book listings for each keyword in parallel
    async.map(keywords, getBooksFromGoogle,
        function (error, results) {
            res.send(results);
        });
});

// callback to get listings for a keyword
function getBooksFromGoogle(keyword, callback) {
    var options = {
        key: process.env.key
    };
    books.search(keyword, options, function (error, results) {
        callback(error, results);
    });
}

module.exports = router;