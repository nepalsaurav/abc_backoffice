<script>
    export let type = "button";
    export let variant = "primary";
    export let size = "md"; // sm, md, lg
    export let outline = false;
    export let classes = "";

    $: btnClass = outline ? `btn-outline-${variant}` : `btn-${variant}`;
</script>

<button {type} class="btn {btnClass} btn-{size} {classes}" on:click>
    <slot></slot>
</button>
