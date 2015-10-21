/**
 * Created by akhil on 11/5/15.
 */
(function ($, W, D) {

    $(D).ready(function ($) {
        google.maps.event.addDomListener(window, 'load', initialize);
        $("#search").click(getJobListing);
        Handlebars.registerHelper('getStarRating', function (rating) {
            var temp = rating * 2;
            temp = Math.round(temp);
            var stars = ['.000', '.125', '.250', '.375', '.500', '.625', '.750', '.875', '1.000', '1.125', '1.250'];
            return stars[temp];
        });

        Handlebars.registerHelper('getEmployerImage', function (src) {
            if (src == null || src == "") {
                return "/images/no-image.jpg";
            }
            return src;

        });
    });

    function initialize() {
        var options = {
            types: ['(regions)'],
            componentRestrictions: {country: "us"}
        };
        var input = document.getElementById("location");
        new google.maps.places.Autocomplete(input, options);
    }

    function getJobListing(event, page) {
        if (page == null) {
            page = 1;
        }
        var data = {};
        var location = $("#location").val();
        var keywords = $("#keywords").val();
        if (location != "") {
            try {
                data["city"] = location.split(",")[0].trim();
                data["state"] = location.split(",")[1].trim();
            } catch (e) {
            }
        }
        if (keywords != "") {
            data['keywords'] = keywords;
        }

        if (jQuery.isEmptyObject(data)) {
            data["noParam"] = "true";
        }

        data['start'] = (page - 1) * 10 + 1;

        $.ajax({
            url: '/jobs',
            data: data,
            dataType: "json",
            type: 'GET',
            success: processJobListings
        });
        return false;
    }

    function processJobListings(response) {
        var template = Handlebars.templates['job'];
        var inner = template({job: response.docs});
        $("#jobs").html(inner).css("display", "inline");
        if (response.numFound == 0) {
            $("#summary").html("No jobs found").css("display", "inline");
        } else {
            $("#summary").html("Showing " + response.start + "-" + Math.min(response.start + 9, response.numFound - 1) + " of " + (response.numFound - 1) + " jobs").css("display", "inline");
        }

        $('#pagination').css("display", "inline");
        $('#pages').empty();
        $('#pages').removeData("twbs-pagination");
        $('#pages').twbsPagination({
            totalPages: Math.ceil(response.numFound / 10),
            visiblePages: Math.min(10, Math.ceil(response.numFound / 10)),
            onPageClick: getJobListing,
            initiateStartPageClick: false,
            startPage: Math.ceil(response.start / 10)
        });
    }

})(jQuery, window, document);