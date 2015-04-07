export default function isParent(child, parent) {
    var match = false;

    if (!parent.children) {
        return false;
    }

    if (!parent.children.length) {
        return false;
    }

    if (parent.children.indexOf(child) >= 0) {
        return true;
    }

    parent.children.forEach(function(n, i) {
        if (isParent(child, n)) {
            match = true;
        }
    });

    return match;
}