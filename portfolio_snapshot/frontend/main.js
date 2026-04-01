import { mount } from 'svelte';
import App from './App.svelte';
import NavBar from "./NavBar.svelte"

mount(App, {
    target: document.getElementById('svelte-app'),
});

mount(NavBar, {
    target: document.getElementById('navbar_svelte'),
});



