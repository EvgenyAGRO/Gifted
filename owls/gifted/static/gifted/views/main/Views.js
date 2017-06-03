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
        var user_rank = Utils.readCookie('user_rank');
        var pictureURL = Utils.readCookie('picture');
        pictureURL = pictureURL.replace(/\"/g, "");

        $picture.attr('src', pictureURL);
        $name[0].innerHTML = 'Hello, ' + given_name + '!  ';
        $rank[0].innerHTML = 'Your Rank is: ' + user_rank;

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

        return '<div class="item  col-xs-4 col-lg-4 grid-group-item">'+
            '<div class="thumbnail">' +
            '<img class="group list-group-image" src=' + '"' + gift.gift_img + '"' + 'alt="" />' +
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

        if (!Utils.readCookie('user_id'))
        {
            NavBar.setLoginButton(); // set listener to login function on login button
        }
        else {
            var given_name = Utils.readCookie('given_name');
            var pictureURL = Utils.readCookie('picture');
            GoogleAuth.onValidatedUser(given_name, pictureURL);
        }
    },
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
        var rank = gift.gift_rank;

        return '<div class="item  col-xs-4 col-lg-4 grid-group-item">'+
                    '<div class="thumbnail">' +
                            '<img class="group list-group-image" src=' + '"' + gift.gift_img + '"' + 'alt="" />' +
                            '<div class="caption">' +
                                    '<h4 class="group inner list-group-item-heading">' +
                                    gift.title + '</h4>' +
                                    '<div class="btn-group">' +
                                         '<button  onclick="ResultsView.likeGift(this.id, 1, this)" class="btn btn-like" id=' + '"' + gift.gift_id + '"' + '>' + 'Like ' +
                                             '<img class="owl-like" src="static/gifted/img/owl_like.png">' +
                                          '</button>' +
                                          '<button  onclick="ResultsView.likeGift(this.id, -1, this)" class="btn btn-dislike" id=' + '"' + gift.gift_id + '"' + '>' + 'Dislike ' +
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


    likeGift: function(giftID, like, el) {
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
                el.disabled = true;
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + '...';
            },
            success: function(data){
                el.disabled = false;
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + newRank;
            },
            error: function(error){
                el.disabled = false;
                $('.likes_' + giftID)[0].innerText = 'Likes: ' + currentRank;
                errorDialog.showDialog(error.responseText);
            },
        });
    },

};


var AboutView = {
    showAboutView: function() {
        Utils.clearView('.main-container');
        var AboutPage = 'static/gifted/inner-templates/AboutPage.html';
        Utils.injectView('.main-container', AboutPage, null, 'background1_80.jpg');

    },
}