import { useEffect, useState } from 'react';
import {
  DataGrid,
  useGridApiRef,
  gridFilteredSortedRowEntriesSelector,
} from '@mui/x-data-grid';
import type {
  GridColDef,
  GridRenderCellParams,
} from '@mui/x-data-grid';
import {
  Dialog,
  Menu,
  MenuItem,
  ThemeProvider,
  CssBaseline,
  createTheme,
  Button,
  IconButton,
  Box
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ReplayIcon from '@mui/icons-material/Replay';
import CheckIcon from '@mui/icons-material/Check';
import ReportGmailerrorredIcon from '@mui/icons-material/ReportGmailerrorred';
import PhotoSizeSelectLargeIcon from '@mui/icons-material/PhotoSizeSelectLarge';


interface Entry {
  id: string;
  prompt_text: string;
  filepath?: string;
  broken?: boolean;
  upscale?: string;
  score_mu?: number;
  score_sigma?: number;
  rank?: number;
  deleted?: boolean;
  width?: number;
  height?: number;
  seed?: number;
  filepath_orig?: string;
}

export default function App() {
  const [rows, setRows] = useState<Entry[]>([]);
  const [visibleRows, setVisibleRows] = useState<Entry[]>([]);
  const [selectedIds, setSelectedIds] = useState<(string | number)[]>([]);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState<number>(0);
  const [rankingMode, setRankingMode] = useState(false);
  const [currentPair, setCurrentPair] = useState<[Entry, Entry] | null>(null);
  const [rankingPool, setRankingPool] = useState<Entry[]>([]);
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);
  const apiRef = useGridApiRef();


  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/entries')
      .then(res => res.json())
      .then(data => {
        setRows(data);
        setTimeout(updateVisibleRows, 0);
      });
  }, []);

  const updateVisibleRows = () => {
    const result = gridFilteredSortedRowEntriesSelector(apiRef).map((x) => x.model) as Entry[];
    setVisibleRows(result);
  };

  const openLightbox = (entryId: string) => {
    updateVisibleRows();
    const index = gridFilteredSortedRowEntriesSelector(apiRef).findIndex((e) => e.id === entryId);
    if (index !== -1) {
      setLightboxIndex(index);
      setLightboxOpen(true);
    }
  };

  const currentImage = visibleRows[lightboxIndex];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!lightboxOpen) return;
      if (e.key === 'ArrowRight') {
        setLightboxIndex((i) => Math.min(i + 1, visibleRows.length - 1));
      } else if (e.key === 'ArrowLeft') {
        setLightboxIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Escape') {
        setLightboxOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [lightboxOpen, visibleRows.length]);

  const toggleBroken = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/entry/${id}/toggle_broken`, {
        method: 'POST',
      });
      if (res.ok) {
        setRows((prevRows) =>
          prevRows.map((row) =>
            row.id === id ? { ...row, broken: !row.broken } : row
          )
        );
        updateVisibleRows();
      } else {
        console.error('Failed to toggle broken status');
      }
    } catch (err) {
      console.error('Error toggling broken status:', err);
    }
  };

  const generate = async (id: string, upscale: boolean) => {
    const endpoint = !upscale ? "generate" : "upscale";
    const addr = `ws://127.0.0.1:8000/ws/${endpoint}/${id}`;
    const ws = new WebSocket(addr);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type == "error") {
        console.error("WebSocket error:", message.message);
        ws.close();
      } else if (message.type == "result") {
        console.log("Image generation complete:", message.data);
        ws.close();
        const data = message.data;
        setRows(prev => {
          // If it's a new entry, append it
          const existingIndex = prev.findIndex(r => r.id === data.id);
          if (existingIndex === -1) {
            return [...prev, data];
          }
          // If the entry exists, update it
          const updated = [...prev];
          updated[existingIndex] = data;
          return updated;
        });
        updateVisibleRows();
      } else {
        console.log("Progress update:", message.message);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket failed", err);
    };
  };

  const deleteEntry = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/entry/${id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setRows((prevRows) =>
          prevRows.map((row) =>
            row.id === id ? { ...row, deleted: true, filepath: "" } : row
          )
        );
        updateVisibleRows();
      } else {
        console.error('Failed to delete entry');
      }
    } catch (err) {
      console.error('Error deleting entry:', err);
    }
  };

  const startRanking = () => {
    const selected = rows.filter((row) => selectedIds.includes(row.id) && !row.deleted && row.filepath);
    if (selected.length < 2) {
      alert("Select at least two entries to compare.");
      return;
    }
    setRankingPool(selected);
    queueNextPair(selected);
    setRankingMode(true);
  };

  const queueNextPair = async (pool = rankingPool) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/trueskill/next_pair', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: pool.map(e => e.id) }),
      });
      if (!res.ok) throw new Error("Failed to fetch next pair");

      const data = await res.json();
      if (!data.a || !data.b) {
        setRankingMode(false);
        return;
      }

      setCurrentPair([data.a, data.b]);
    } catch (err) {
      console.error("Next pair error:", err);
      setRankingMode(false);
    }
  };

  const handleRankVote = async (winnerIndex: number | null) => {
    const [a, b] = currentPair!;
    let body;

    if (winnerIndex === null) {
      body = { draw: [a.id, b.id] };
    } else {
      const winner = winnerIndex === 0 ? a.id : b.id;
      const loser = winnerIndex === 0 ? b.id : a.id;
      body = { winner, loser };
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/api/trueskill/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error("Failed to update ranking");

      const updated = await res.json();
      if (Array.isArray(updated)) {
        setRows(prev =>
          prev.map(row =>
            updated.find(u => u.id === row.id) || row
          )
        );
      }

      queueNextPair();
    } catch (err) {
      console.error("Ranking update failed:", err);
      setRankingMode(false);
    }
  };



  const bulkDelete = () => {
    console.log('Bulk delete:', selectedIds);
    // TODO
  };

  const columns: GridColDef[] = [
    {
      field: 'filepath',
      headerName: 'Thumbnail',
      width: 100,
      renderCell: (params: GridRenderCellParams) =>
        params.value ? (
          <img
            src={'http://127.0.0.1:8000/images/' + params.value}
            alt=""
            style={{ width: 120, height: 'auto', cursor: 'pointer' }}
            onClick={() => openLightbox(params.row.id)}
          />
        ) : (
          'N/A'
        )
    },
    { field: 'prompt_text', headerName: 'Prompt', width: 200, flex: 1, },
    { field: 'upscale', headerName: 'Upscale', width: 100, flex: 0, },
    { field: 'broken', headerName: 'Broken', width: 100, flex: 0, },
    { field: 'deleted', headerName: 'Deleted', width: 100, flex: 0, },
    { field: 'score_mu', headerName: 'μ', width: 100, type: 'number', flex: 0, },
    { field: 'score_sigma', headerName: 'σ', width: 100, type: 'number', flex: 0, },
    { field: 'rank', headerName: 'rank', width: 100, type: 'number', flex: 0, },
    { field: 'width', headerName: 'Width', width: 100, type: 'number', flex: 0, },
    { field: 'height', headerName: 'Height', width: 100, type: 'number', flex: 0, },
    { field: 'seed', headerName: 'Seed', width: 100, flex: 0, },
    {
      field: 'actions',
      headerName: 'Actions',
      sortable: false,
      filterable: false,
      width: 180,
      renderCell: (params: GridRenderCellParams) => {
        const { id, broken, deleted, filepath, upscale } = params.row;

        return (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              onClick={() => toggleBroken(id)}
              title={broken ? 'Mark as OK' : 'Mark as Broken'}
              disabled={deleted || !filepath}
            >
              {broken ? <CheckIcon fontSize="small" /> : <ReportGmailerrorredIcon fontSize="small" />}
            </IconButton>
            <IconButton onClick={() => generate(id, false)} title="(Re-)generate">
              <ReplayIcon fontSize="small" />
            </IconButton>
            <IconButton
              onClick={() => generate(id, true)}
              title="Upscale"
              disabled={deleted || !filepath || upscale == "is_upscale"}
            >
              <PhotoSizeSelectLargeIcon fontSize="small" />
            </IconButton>
            <IconButton
              onClick={() => deleteEntry(id)}
              title="Delete"
              disabled={deleted}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        );
      }

    }
  ];

  const darkTheme = createTheme({
    palette: {
      mode: 'dark'
    }
  });

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ padding: 2 }}>
        {!rankingMode || !currentPair ? (
          <Box sx={{ height: '95vh', width: '98vw' }} onContextMenu={(e) => {
            e.preventDefault();
            if (selectedIds.length > 0) {
              setContextMenu(
                contextMenu === null
                  ? {
                    mouseX: e.clientX + 2,
                    mouseY: e.clientY - 6,
                  }
                  : null
              );
            }
          }}>
            <DataGrid
              apiRef={apiRef}
              rows={rows}
              columns={columns}
              getRowId={(row) => row.id}
              checkboxSelection
              disableRowSelectionOnClick
              onSortModelChange={updateVisibleRows}
              onFilterModelChange={updateVisibleRows}
              onPaginationModelChange={updateVisibleRows}
              onRowSelectionModelChange={(ids) => {
                setSelectedIds(Array.from(ids.ids));
                updateVisibleRows();
              }}
              initialState={{
                filter: {
                  filterModel: {
                    items: [{ field: 'deleted', operator: 'equals', value: 'false' }],
                  },
                },
              }}
            />
            <Menu
              open={contextMenu !== null}
              onClose={() => setContextMenu(null)}
              anchorReference="anchorPosition"
              anchorPosition={
                contextMenu !== null
                  ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                  : undefined
              }
            >
              <MenuItem
                onClick={() => {
                  setContextMenu(null);
                  startRanking();
                }}
              >
                Rank Selected
              </MenuItem>
              <MenuItem
                onClick={() => {
                  setContextMenu(null);
                  bulkDelete();
                }}
              >
                Delete Selected
              </MenuItem>
            </Menu>
          </Box>) : (<>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4, p: 2 }}>
              {currentPair.map((entry, i) => (
                <img
                  key={entry.id}
                  src={'http://127.0.0.1:8000/images/' + entry.filepath}
                  alt={entry.prompt_text}
                  style={{
                    maxWidth: '45vw',
                    maxHeight: '80vh',
                    width: 'auto',
                    objectFit: 'contain',
                    cursor: 'pointer',
                    border: '4px solid transparent',
                  }}
                  onClick={() => handleRankVote(i)}
                />
              ))}
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                maxWidth: '90vw',
                mt: 2,
              }}
            >
              <Box sx={{ flex: 1 }} />

              <Box sx={{ flex: 0 }}>
                <Button variant="outlined" onClick={() => handleRankVote(null)}>
                  Draw
                </Button>
              </Box>

              <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={() => setRankingMode(false)}>Exit</Button>
              </Box>
            </Box>
          </>
        )
        }
        <Dialog open={lightboxOpen} onClose={() => setLightboxOpen(false)} maxWidth="lg">
          {currentImage && (
            <>
              <img
                src={'http://127.0.0.1:8000/images/' + currentImage.filepath}
                alt={currentImage.prompt_text}
                style={{
                  maxWidth: '90vw',
                  maxHeight: '90vh',
                  objectFit: 'contain',
                  cursor: 'pointer'
                }}
                onClick={() => setLightboxOpen(false)}
              />
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 16,
                  right: 16,
                  display: 'flex',
                  gap: 1,
                  backgroundColor: 'rgba(0, 0, 0, 0.5)',
                  borderRadius: 1,
                  padding: 1,
                }}


              >
                <IconButton
                  onClick={() => toggleBroken(currentImage.id)}
                  title={currentImage.broken ? 'Mark as OK' : 'Mark as Broken'}
                  disabled={currentImage.deleted || !currentImage.filepath}
                >
                  {currentImage.broken ? <CheckIcon /> : <ReportGmailerrorredIcon />}
                </IconButton>
                <IconButton onClick={() => generate(currentImage.id, false)} title="(Re-)generate">
                  <ReplayIcon />
                </IconButton>
                <IconButton
                  onClick={() => generate(currentImage.id, true)}
                  title="Upscale"
                  disabled={currentImage.deleted || !currentImage.filepath || currentImage.upscale == "is_upscale"}
                >
                  <PhotoSizeSelectLargeIcon fontSize="small" />
                </IconButton>
                <IconButton
                  onClick={() => {
                    deleteEntry(currentImage.id);
                    setLightboxIndex((i) => Math.min(i + 1, visibleRows.length - 1));
                  }}
                  title="Delete"
                  disabled={currentImage.deleted}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </>
          )}
        </Dialog>
      </Box>
    </ThemeProvider>
  );
}
