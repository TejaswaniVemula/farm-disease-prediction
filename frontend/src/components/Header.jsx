import { Box, Typography } from "@mui/material";
export default function Header(){
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="h4" sx={{ lineHeight: 1.15 }}>
        Farm Animal Disease Prediction
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
        Bilingual Decision Support (English / తెలుగు) • Disease Prediction and  Risk Analysis
      </Typography>
    </Box>
  );
}
