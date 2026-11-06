import { render } from "preact";
import { applySeriesColors } from "./common/colors.js";
import { App } from "./weather-app.jsx";
import "../styles.css";

applySeriesColors();
render(<App />, document.getElementById("app"));