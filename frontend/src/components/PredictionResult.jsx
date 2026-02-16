import { Box, Card, CardContent, Chip, Divider, Grid, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";

function riskColor(text=""){
  const t = (text||"").toLowerCase();
  if(t.includes("high")) return "error";
  if(t.includes("medium")) return "warning";
  if(t.includes("low")) return "success";
  return "default";
}

export default function PredictionResult({ result }){
  if(!result) return null;

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>Output</Typography>

        <Typography variant="body2"><b>Animal:</b> {result.animal?.display || "—"}</Typography>

        <Box sx={{ mt: 1, display:"flex", flexWrap:"wrap", gap:1 }}>
          {result.symptoms?.map(s => (
            <Chip key={s.en} label={s.display} variant="outlined" />
          ))}
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Top Predictions</Typography>

        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Disease</TableCell>
              <TableCell align="right">Probability</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {result.predictions?.map((p, idx) => (
              <TableRow key={idx} sx={idx===0 ? { backgroundColor:"rgba(21, 101, 192, 0.08)" } : undefined}>
                <TableCell sx={idx===0 ? { fontWeight:700 } : undefined}>{p.disease?.display || "—"}</TableCell>
                <TableCell align="right" sx={idx===0 ? { fontWeight:700 } : undefined}>
                  {typeof p.probability_percent === "number" ? `${p.probability_percent.toFixed(2)}%` : `${p.probability_percent}%`}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Risk Analysis</Typography>
        <Box sx={{ display:"flex", alignItems:"center", gap:1, flexWrap:"wrap" }}>
          <Chip label={result.risk?.overall?.display || "—"} color={riskColor(result.risk?.overall?.display)} sx={{ fontWeight:700 }} />
          <Typography variant="body2" color="text.secondary">{result.risk?.explanation || ""}</Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Prevention</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary">English</Typography>
                    <Typography variant="body2">{result.prevention?.en || "—"}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary">తెలుగు</Typography>
                    <Typography variant="body2">{result.prevention?.te || "—"}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Precautions</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary">English</Typography>
                    <Typography variant="body2">{result.precautions?.en || "—"}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary">తెలుగు</Typography>
                    <Typography variant="body2">{result.precautions?.te || "—"}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}
