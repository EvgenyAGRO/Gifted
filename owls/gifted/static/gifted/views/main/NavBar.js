/**
 * Created by ysayag on 09/05/2017.
 */
var NavBar = {
    setLoginButton: function() {
        var $login = $('#login-button');
        auth2.attachClickHandler($login[0], {},
            GoogleAuth.onSignIn, function(e) {console.error(e.error)});
    },

    hideTopButtons: function() {
        var $login = $('#login-button'); var $logout = $('#logout-button'); var $welcome = $('#welcome');
        var $search = $('#search-button'); var $upload = $('#upload-button');
        var $about = $('#about-button');

        $logout.hide();
        $logout.off('click');
        $search.hide();
        $upload.hide();
        $login.show();
        $about.show();
        $welcome.hide();
        $welcome.off('click');
        $welcome[0].innerText = '';
    },

    hideAllButtons: function() {
        var $login = $('#login-button'); var $logout = $('#logout-button'); var $welcome = $('#welcome');
        var $search = $('#search-button'); var $upload = $('#upload-button');
        var $about = $('#about-button');

        $logout.hide();
        $logout.off('click');
        $search.hide();
        $upload.hide();
        $login.hide();
        $welcome.hide();
        $welcome.off('click');
        $about.hide();
        $welcome[0].innerText = '';
    },

    showTopButtons: function() {
        var $login = $('#login-button'); var $logout = $('#logout-button');
        var $search = $('#search-button'); var $upload = $('#upload-button');
        var $about = $('#about-button');

        $login.hide();
        $logout.show();
        $logout.click(GoogleAuth.signOut);
        $search.show();
        $upload.show();
        $about.show();
    },

    showWelcome: function(userName, pictureURL) {
        var introHeader = 'static/gifted/inner-templates/introHeader.html';
        pictureURL = pictureURL.replace(/\"/g, "");
        var $welcome = $('#welcome');
        //TODO: check if user is in DB Already, if so present 'welcome back' message or something similar
        $welcome.hide();
        var $welcomeText = $('<div></div>');
        $welcomeText[0].innerText = 'Welcome, ' + userName + '!  ';
        var img = $('<img class="user-img">');
        img.attr('src', pictureURL);
        $welcomeText.css('padding-left', '5px');
        img.appendTo('#welcome');
        $welcomeText.appendTo('#welcome');
        $welcome.show();
        $welcome.click(ProfileView.showProfilePage)
    },

    showIntroHeader: function() {
        Utils.clearMainView('.intro-header');
        var IntroHeader = 'static/gifted/inner-templates/IntroHeader.html';
        Utils.injectMainView('.intro-header', IntroHeader);
    },

};