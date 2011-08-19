
$(function () {
    $(".breadcrumb").click(function() {
        var clicked = this;
        var clicked_idx = 0;
        var crumbs = $(".breadcrumb");
        crumbs.each(function (i) {
            if (this != clicked) return;
            clicked_idx = i+1;
            return false;
        });

        url = crumbs.slice(0, clicked_idx).map(function() {return $(this).text();}).get().join("/");
        dest = $("#base_url").attr("href") + url + "/";
        window.location = dest;
        //alert();


        query = crumbs.map(function () { 
            return this == clicked ? "*" : $(this).text(); 
        }).get().join("/");
        //alert(query);
    });
});
