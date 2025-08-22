// Alterna a largura do sidenav
function moveSideBar() {
    const sidenav = document.getElementById("mySidenav");
    const main = document.getElementById("main");

    if (sidenav.style.width === "160px") {
        sidenav.style.width = "0px";
        main.style.marginLeft = "60px"; 
    } else {
        sidenav.style.width = "160px";
        main.style.marginLeft = "160px";
    }
}



