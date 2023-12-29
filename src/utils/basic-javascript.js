// Seed random generator
function splitMix(a) {
  return function() {
    a |= 0; a = a + 0x9e3779b9 | 0;
    var t = a ^ a >>> 16; t = Math.imul(t, 0x21f0aaad);
        t = t ^ t >>> 15; t = Math.imul(t, 0x735a2d97);
    return ((t = t ^ t >>> 15) >>> 0) / 4294967296;
  }
}

export function seededRandom( seed ) {
  return splitMix( seed )();
}

export function shuffle( array, seed=0 ) {
  for (let i = array.length-1; i>0; i--) {

    let j;
    // if no seed
    if ( seed==0 ) {
      // console.log("no seed ");
      j = Math.floor(Math.random() * (i+1));
    }
    // if seed set
    else { 
      // console.log("yes seed ");
      var rng = seededRandom( seed );
      j = Math.floor(rng * (i+1));
    }

    // wizard
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

export function slugify(str) {
  return String(str)
    .normalize('NFKD') // split accented characters into their base characters and diacritical marks
    .replace(/[\u0300-\u036f]/g, '') // remove all the accents, which happen to be all in the \u03xx UNICODE block.
    .trim() // trim leading or trailing whitespace
    .toLowerCase() // convert to lowercase
    .replace(/[^a-z0-9 -]/g, '') // remove non-alphanumeric characters
    .replace(/\s+/g, '-') // replace spaces with hyphens
    .replace(/-+/g, '-'); // remove consecutive hyphens
}

export function csvStringToArray( simpleCSV ) {
  return simpleCSV.split(',').map( item => item.trim() );
}
