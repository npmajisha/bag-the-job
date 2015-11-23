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

        Handlebars.registerPartial('getMoreInfo', Handlebars.templates['moreinfo']);
        Handlebars.registerPartial('getBooks', Handlebars.templates['book']);
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

        data['start'] = (page - 1) * 10;

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

        updateEventListeners();

        updateSummary(response);

        updatePagination(response);
    }

    function updateSummary(response) {
        if (response.numFound == 0) {
            $("#summary").html("No jobs found").css("display", "inline");
        } else {
            $("#summary").html("Showing " + (response.start + 1) + "-" + Math.min(response.start + 10, response.numFound) + " of " + (response.numFound) + " jobs").css("display", "inline");
        }
    }

    function updatePagination(response) {
        $('#pagination').css("display", "inline");
        var pages = $('#pages');
        pages.empty();
        pages.removeData("twbs-pagination");
        pages.twbsPagination({
            totalPages: Math.ceil(response.numFound / 10),
            visiblePages: Math.min(10, Math.ceil(response.numFound / 10)),
            onPageClick: getJobListing,
            initiateStartPageClick: false,
            startPage: Math.max(Math.ceil((response.start + 1) / 10), 1)
        });
    }

    function updateEventListeners() {
        $(".moreinfo").click(showDetailsModal);
    }

    function showDetailsModal(event) {
        var template = Handlebars.templates['moreinfo'];
        var moreinfo = $("#moreinfo");
        moreinfo.html(template());
        updateModalTitle(event.target);
        updateModalTags(event.target);
        updateBooksCarousel(getTags(event.target));
        updateCourseCarousel(getTags(event.target));
        moreinfo.modal('toggle');

    }

    function getTags(jobDetails) {
        //return jobDetails.dataset.tags.split(",");
        return ['3D Graphics', 'AJAX', 'Algebra', 'Algorithms', 'Amazon EC2', 'Analysis', 'Analytic', 'Analytics', 'Android'];
    }

    function updateModalTitle(jobDetails) {
        $("#modal-title").text(jobDetails.dataset.title + ' - ' + jobDetails.dataset.employer + ' ' + jobDetails.dataset.city + ', '
            + jobDetails.dataset.state);
    }

    function updateModalTags(jobDetails) {
        var tags = getTags(jobDetails);
        var template = Handlebars.templates['tags'];
        $("#modal-tags").html(template({tag: tags}));
        $(".skill-tag").click(function (event) {
            updateBooksCarousel([($(event.target)).text()]);
            updateCourseCarousel([($(event.target)).text()])
        });
    }

    function updateBooksCarousel(tags) {
        //var tags = ['3D Graphics','AJAX','Algebra','Algorithmic Thinking','Algorithms','Amazon EC2','Analysis','Analytic','Analytical Techniques','Analytics','ANCOVA','Android'];
        $.ajax({
            url: '/books',
            data: {keywords: tags},
            dataType: "json",
            type: 'GET',
            success: function (response) {
                var books = [];
                for (var i = 0; i < response.length; i++) {
                    books = books.concat(response[i]);
                }
                var template = Handlebars.templates['book'];
                var modalBooks = $("#modal-books");
                modalBooks.html("");
                modalBooks.removeClass();
                modalBooks.html(template({book: books}));
                modalBooks.slick({
                    dots: true,
                    infinite: false,
                    slidesToShow: 3,
                    slidesToScroll: 3,
                    initialSlide: 1
                });
                modalBooks.slick('slickGoTo', 0);
            }
        });
    }

    function updateCourseCarousel(tags) {
        $.ajax({
            url: '/courses',
            data: {keywords: tags},
            dataType: "json",
            type: 'GET',
            success: function (response) {
                var courses = [];
                for (var i = 0; i < response.length; i++) {
                    courses = courses.concat(response[i].response.docs);
                }
                var template = Handlebars.templates['courses'];
                var modalCourses = $("#modal-courses");
                modalCourses.html("");
                modalCourses.removeClass();
                modalCourses.html(template({course: courses}));
                modalCourses.slick({
                    dots: true,
                    infinite: false,
                    slidesToShow: 3,
                    slidesToScroll: 3,
                    initialSlide: 1
                });
                modalCourses.slick('slickGoTo', 0);
            }
        });
    }

})(jQuery, window, document);