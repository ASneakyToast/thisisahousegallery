/* I thought I could do it here but I'm a little like huh, how's this gonna work?
 * Actually this will work if I put the json file in the public folder
 * Which is actually perfered maybe?
 * For now I'll just export individual functions to be used here

  const exhibition_image_data = {
    thisisalivingroom: "idk how this ones gonna work...",
  }

 */

/* Now I'm also just like, hey fuck it let's just include
 * the exhibition name within the image that gets passed 

  export function GetImageSrc( exhibition_title, filename ) {
    return "/exhibitions/"
  }

  */

export function TestWithParams( AString ) {
  console.log( AString );
}

export function AnotherFunction() {
  console.log("another one!");
}

export function SuperCoolFunction() {
  console.log("what's up, I'm a function from anohter file here to help!");
}
