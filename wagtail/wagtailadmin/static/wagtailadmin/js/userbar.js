/* No jQuery to speed up loading */
document.addEventListener('DOMContentLoaded', function(){
    var body = document.querySelectorAll('body')[0];
    var className = 'ready';

    if (body.classList){
        body.classList.add(className);
    }else{
        body.className += ' ' + className;
    }
});