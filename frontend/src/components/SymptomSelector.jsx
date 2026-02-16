import { useMemo, useState } from "react";
import { Box, Checkbox, Chip, Divider, FormControlLabel, InputAdornment, TextField, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

export default function SymptomSelector({ allSymptoms, selected, setSelected, min=3, max=8, disabled=false }){
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if(!q) return allSymptoms;
    return allSymptoms.filter(s =>
      (s.display||"").toLowerCase().includes(q) ||
      (s.en||"").toLowerCase().includes(q) ||
      (s.te||"").toLowerCase().includes(q)
    );
  }, [allSymptoms, query]);

  const toggle = (en) => {
    if(disabled) return;
    const exists = selected.includes(en);
    if(exists) return setSelected(selected.filter(x=>x!==en));
    if(selected.length >= max) return;
    setSelected([...selected, en]);
  };

  const removeChip = (en) => {
    if(disabled) return;
    setSelected(selected.filter(x=>x!==en));
  };

  const selectedDisplay = useMemo(() => {
    const map = new Map(allSymptoms.map(s => [s.en, s]));
    return selected.map(en => map.get(en) || { en, te:"—", display:`${en} / —` });
  }, [selected, allSymptoms]);

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
        Symptoms (select {min} to {max})
      </Typography>

      <TextField
        fullWidth
        size="small"
        value={query}
        onChange={(e)=>setQuery(e.target.value)}
        placeholder="Search symptoms (English / తెలుగు)"
        disabled={disabled}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" />
            </InputAdornment>
          )
        }}
      />

      <Box sx={{ mt: 1, display:"flex", flexWrap:"wrap", gap:1 }}>
        {selectedDisplay.map(s => (
          <Chip key={s.en} label={s.display} onDelete={disabled?undefined:()=>removeChip(s.en)} color="primary" variant="outlined" />
        ))}
        {selected.length===0 && (
          <Typography variant="body2" color="text.secondary">No symptoms selected yet.</Typography>
        )}
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ maxHeight: 360, overflow:"auto", pr:1, display:"grid", gridTemplateColumns:{ xs:"1fr", md:"1fr 1fr" }, gap:0.5 }}>
        {filtered.map(s => {
          const checked = selected.includes(s.en);
          const blocked = !checked && selected.length >= max;
          return (
            <FormControlLabel
              key={s.en}
              control={<Checkbox checked={checked} onChange={()=>toggle(s.en)} disabled={disabled || blocked} />}
              label={
                <Typography variant="body2">
                  {s.display}
                  {blocked ? <Typography component="span" variant="caption" color="error" sx={{ ml: 1 }}>(max {max})</Typography> : null}
                </Typography>
              }
            />
          );
        })}
        {filtered.length===0 && (
          <Typography variant="body2" color="text.secondary">No symptoms match your search.</Typography>
        )}
      </Box>
    </Box>
  );
}
