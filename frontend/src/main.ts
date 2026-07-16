import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { countup } from "./directives/countup";
import { reveal } from "./directives/reveal";
import { router } from "./router";
import "./styles.css";

createApp(App).use(createPinia()).use(router).directive("reveal", reveal).directive("countup", countup).mount("#app");
