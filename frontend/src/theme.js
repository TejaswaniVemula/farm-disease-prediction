import { createTheme } from "@mui/material/styles";
const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1565c0" },
    secondary: { main: "#2e7d32" },
    background: { default: "#fafafa" },
  },
  shape: { borderRadius: 14 },
  typography: {
    fontFamily: ["Inter","system-ui","Segoe UI","Roboto","Arial","sans-serif"].join(","),
    h4: { fontWeight: 700 },
    h6: { fontWeight: 700 },
  },
  components: { MuiCard: { styleOverrides: { root: { boxShadow: "0 6px 24px rgba(0,0,0,0.06)" }}}}
});
export default theme;
