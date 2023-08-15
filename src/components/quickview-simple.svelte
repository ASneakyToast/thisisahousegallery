<section id="testing" class="quickview_simple">
  <img />
  <h1>Big Text box</h1>
  <p>{ image_url }</p>
  <p>{ alt_text }</p>
  <p>{ caption }</p>
  <button on:click={ destroyThis }>DESTROY ME</button>
</section>

<script>
  //const quickview_simple_element = document.querySelector(".quickview_simple");
  import { onMount } from 'svelte';
  import { get_current_component } from 'svelte/internal';

  export let image_url = "Placeholder url"; 
  export let alt_text = "Image alt txt";
  export let caption = "default caption";

  let thisComponent = get_current_component();

  function destroyThis() {
    console.log( "smash time!" );
    thisComponent.$destroy();
  }

  onMount(() => {
    console.log('this component has mounted');
    const quickview_simple_element = document.querySelector(".quickview_simple");

    quickview_simple_element.addEventListener( "quickview-simple--open", ({ detail }) => {
      console.log( "heard it!" );

      // debug data
      console.log( detail );
      console.log( item );

      // apply data
      // img element set html or something
    });
  });

</script>
