/**
 * Created by ysayag on 09/05/2017.
 */

var ProfileView = {

    showProfilePage: function(gifts) {
        window.userGifts = gifts
        Utils.clearView('.main-container');
        var profilePage = 'static/gifted/inner-templates/profilePage.html';
        Utils.injectView('.main-container', profilePage, ProfileView.onProfilePageInjected, 'background1_80.jpg');

    },

    onProfilePageInjected: function() {
        var $picture = $('#profile-picture');
        var $name = $('#profile-name');
        var $rank = $('#profile-rank');
        var given_name = Utils.readCookie('given_name');
        var pictureURL = Utils.readCookie('picture');
        pictureURL = pictureURL.replace(/\"/g, "");

        $picture.attr('src', pictureURL);
        $name[0].innerHTML = 'Hello, ' + given_name + '!  ';
        ProfileView.getProfileRankBar().appendTo($rank);
        ProfileView.insertGifts(window.userGifts);

    },

    insertGifts: function(GiftsObject) {
        var $products = $('#products');
        if (!GiftsObject || !GiftsObject.length) {
            return $($products).append($('<h3 class="h3_home wow fadeIn" data-wow-delay="0.4s">No Gifts</h3>'));
        }
        var i;
        for (i = 0; i < GiftsObject.length; i++) {
            $($products).append($(ProfileView.createGiftElement(GiftsObject[i])))
        }
    },

    createGiftElement: function(gift) {
        var img_url = gift.gift_img || 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcReMxYxGBiScljKXJ3De1t8vLewNDml3yDPYlgL_19Jkzgh6VyZ2mtTUA';


        return '<div class="item  col-xs-4 col-lg-4 grid-group-item">'+
            '<div class="thumbnail">' +
            '<img class="group list-group-image" src=' + '"' + img_url + '"' + 'alt="" />' +
            '<div class="caption">' +
            '<h4 class="group inner list-group-item-heading">' +
            gift.title + '</h4>' +
            '<div class="row">' +
            '<div class="col-xs-12 col-md-6">' +
            '<p class="lead">' + 'Price: ' +
            gift.price + ' ₪' + '</p>' +
            '</div>' +
            '<div class="col-xs-12 col-md-6">' +
            '<p class="lead">' +
            'Likes: ' + gift.gift_rank +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="row">' +
            gift.description +
            '</div>' +
            '</div>' +
            '</div>' +
            '</div>'
    },

    getProfileRankBar: function() {
        var userRank = Utils.getUserRank();
        var barValue = Math.max(35,userRank);
        barValue = Math.min(100,barValue) + 35;
        var rank_color = Utils.getRankColor();
        if (rank_color != 'red') {
            return $(
                '<div class="progress progress-rank-profile">' +
                '<div class="progress-bar ' + rank_color + '-gifter" role="progressbar" aria-valuenow="' + barValue + '"' +
                'aria-valuemin="0" aria-valuemax="100" style="width:' + barValue + '%">' +
                '<h4 class="profile-rank-value">' + 'Rank: ' + userRank + ' (' + Utils.capitalizeFirstLetter(rank_color) + ' User)' +'</h4>' +
                '</div>' +
                '</div>'
            );
        }
        else {
            return $(
                '<div class="progress progress-rank-profile">' +
                '<div class="progress-bar red-gifter" role="progressbar" aria-valuenow="100"' +
                'aria-valuemin="0" aria-valuemax="100" style="width:100%">' +
                '<h4 class="profile-rank-value">' + 'User under warning!' + ' (Rank: ' + userRank + ')</h4>' +
                '</div>' +
                '</div>'
            );
        }
    }
};


var MainView = {

    showMainView: function() {
        Utils.clearView('.main-container');
        var IntroHeader = 'static/gifted/inner-templates/IntroHeader.html';
        Utils.injectView('.main-container', IntroHeader, null, 'background1.jpg');
    },

    initMainView: function() {
        var $home = $('#home-button');

        MainView.showMainView();
        $home.click(MainView.showMainView);

        // check if cookie from server exists and valid
        if (Utils.readCookie('expiry_time') && MainView.checkExpiry())
        {
            var given_name = Utils.readCookie('given_name');
            var pictureURL = Utils.readCookie('picture');
            GoogleAuth.onValidatedUser(given_name, pictureURL);
        }
        else {
            MainView.deleteAllCookies();

            NavBar.setLoginButton(); // set listener to login function on login button

        }
    },

    checkExpiry: function() {
        var now = new Date();
        var now_utc = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),  now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds());
        var expiry_time_str = Utils.readCookie('expiry_time').replace(/\"/g, "")
        var expiry_time = new Date(expiry_time_str);
        return now_utc.getTime() <= expiry_time.getTime();


    },

    deleteAllCookies: function () {
    var cookies = document.cookie.split(";");

    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");
        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}
};

var ResultsView = {

    showResultsPage: function(gifts) {
        window.resultsGifts = gifts;
        Utils.clearView('.main-container');
        var ResultsPage = 'static/gifted/inner-templates/searchResultsPage.html';
        Utils.injectView('.main-container', ResultsPage, ResultsView.onResultsPageInjected, 'background1_80.jpg');

    },

    onResultsPageInjected: function() {
        ResultsView.insertGifts(window.resultsGifts);

    },

    insertGifts: function(GiftsObject) {
        var $products = $('#products');

        if (!GiftsObject || !GiftsObject.length) {
            return $($products).append($('<h3 class="h3_home wow fadeIn" data-wow-delay="0.4s">No Results</h3>'));
        }
        var i;
        for (i = 0; i < GiftsObject.length; i++) {
            $($products).append($(ResultsView.createGiftElement(GiftsObject[i])));
        }
    },

    createGiftElement: function(gift) {
        var img_url = gift.gift_img || 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcReMxYxGBiScljKXJ3De1t8vLewNDml3yDPYlgL_19Jkzgh6VyZ2mtTUA';
        var disableLike = false;
        var disableDislike = false;
        var liked_users = JSON.parse(gift.liked_users);
        var userID = Utils.readCookie('user_id');
        var rated_by_user = _.find(liked_users, { 'user_id': userID});
        if (rated_by_user) {
            if (rated_by_user.is_like) disableLike = true;
            else disableDislike = true;
        }


        return '<div class="item  col-xs-4 col-lg-4 grid-group-item">'+
                    '<div class="thumbnail">' +
                            '<img class="help-us help_' + gift.gift_id + '" onclick="ResultsView.showQuestionDialog(this)" src="static/gifted/img/help-us1.jpeg">' +
                            '<img class="group list-group-image" src=' + '"' + img_url + '"' + 'alt="" />' +
                            '<div class="caption">' +
                                    '<h4 class="group inner list-group-item-heading">' +
                                    gift.title + '</h4>' +
                                    '<div class="btn-group">' +
                                         '<button  onclick="ResultsView.likeGift(1, this)" class="btn btn-like" like-id=' + '"' + gift.gift_id + '"' + (disableLike ? 'disabled' : '') + '>' + 'Like ' +
                                             '<img class="owl-like" src="static/gifted/img/owl_like.png">' +
                                          '</button>' +
                                          '<button  onclick="ResultsView.likeGift(-1, this)" class="btn btn-dislike" dislike-id=' + '"' + gift.gift_id + '"' + (disableDislike ? 'disabled' : '') + '>' + 'Dislike ' +
                                             '<img class="owl-like" src="static/gifted/img/owl_like.png">' +
                                          '</button>' +
                                    '</div>' +
                                 '<div class="row">' +
                                     '<div class="col-xs-12 col-md-6">' +
                                         '<p class="lead">' + 'Price: ' +
                                        gift.price + ' ₪' + '</p>' +
                                    '</div>' +
                                     '<div class="col-xs-12 col-md-6">' +
                                        '<p class="lead likes_' + gift.gift_id + '">' +
                                           'Likes: ' + gift.gift_rank +
                                        '</p>' +
                                    '</div>' +
                                 '</div>' +
                                '<div class="row">' +
                                          gift.description +
                                '</div>' +
                            '</div>' +
                    '</div>' +
              '</div>'
    },


    likeGift: function(like, el) {
        var giftID = el.getAttribute('like-id') || el.getAttribute('dislike-id');
        var giftObject = $.grep(window.resultsGifts, function(e){ return e.gift_id == giftID; })[0];
        var currentRank = giftObject.gift_rank;
        var newRank = giftObject.gift_rank = currentRank + like;
        var obj = {};
        obj.gift_id = giftID;
        obj.like = like;
        $.ajax({
            type: "POST",
            url: "http://localhost:63343/like/",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(obj),
            dataType: "json",
            beforeSend: function(data){
                $(el).addClass(like == 1 ? 'like-glow' : 'dislike-glow');
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + '...';
            },
            success: function(data){
                var negEl = like == 1 ? $('[dislike-id="' + giftID + '"]')[0] : $('[like-id="' + giftID + '"]')[0];
                el.disabled = true;
                negEl.disabled = false;

                $(el).removeClass(like == 1 ? 'like-glow' : 'dislike-glow');
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + newRank;
            },
            error: function(error){
                $(el).removeClass(like == 1 ? 'like-glow' : 'dislike-glow');
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + currentRank;
                errorDialog.showDialog(error.responseText);
            },
        });
    },
    showQuestionDialog: function(el) {
        var giftID = parseInt(el.className.replace(/[^0-9\.]/g, ''), 10);
        var giftObject = $.grep(window.resultsGifts, function(e){ return e.gift_id == giftID; })[0];
        var giftRelationship = giftObject.relationship;
        $(function () {
            $("#question-relationship-score").rateYo({
                starWidth: "40px"
            });

        });
        QuestionDialog.showDialog(giftRelationship);
    },

};

var AboutView = {
    showAboutView: function() {
        Utils.clearView('.main-container');
        var AboutPage = 'static/gifted/inner-templates/AboutPage.html';
        Utils.injectView('.main-container', AboutPage, null, 'background1_80.jpg');

    },
};

var FAQView = {
    showFAQView: function () {
        Utils.clearView('.main-container');
        var FAQPage = 'static/gifted/inner-templates/faqPage.html';
        Utils.injectView('.main-container', FAQPage, null, 'background1_80.jpg');
    }
};