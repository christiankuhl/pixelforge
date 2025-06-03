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

interface Entry {
  id: string;
  prompt_text: string;
  filepath?: string;
  broken?: boolean;
  upscale?: string;
  score_mu?: number;
  score_sigma?: number;
  deleted?: boolean;
  width?: number;
  height?: number;
  seed?: number;
}

export default function App() {
  const [rows, setRows] = useState<Entry[]>([]);
  const [visibleRows, setVisibleRows] = useState<Entry[]>([]);
  const [selectedIds, setSelectedIds] = useState<(string | number)[]>([]);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState<number>(0);

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

  const toggleBroken = (id: string, broken: string) => {
    console.log('Mark broken:', id);
    // TODO: replace with API call or state update
  };

  const regenerate = (id: string) => {
    console.log('Regenerate:', id);
    // TODO
  };

  const deleteEntry = (id: string) => {
    console.log('Delete:', id);
    // TODO
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
            src={params.value}
            alt=""
            style={{ width: 50, height: 'auto', cursor: 'pointer' }}
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
        const { id, broken, deleted, filepath } = params.row;

        return (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              onClick={() => toggleBroken(id, broken)}
              title={broken ? 'Mark as OK' : 'Mark as Broken'}
              disabled={deleted || !filepath}
            >
              {broken ? <CheckIcon fontSize="small" /> : <ReportGmailerrorredIcon fontSize="small" />}
            </IconButton>
            <IconButton onClick={() => regenerate(id)} title="Regenerate">
              <ReplayIcon fontSize="small" />
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
        {selectedIds.length > 0 && (
          <Box sx={{ marginBottom: 2 }}>
            <Button variant="contained" color="secondary" onClick={bulkDelete}>
              Delete Selected
            </Button>
          </Box>
        )}
        <Box sx={{ height: '95vh', width: '98vw' }}>
          <DataGrid
            apiRef={apiRef}
            rows={rows}
            columns={columns}
            getRowId={(row) => row.id}
            checkboxSelection
            onSortModelChange={updateVisibleRows}
            onFilterModelChange={updateVisibleRows}
            onPaginationModelChange={updateVisibleRows}
            onRowSelectionModelChange={(ids) => {
              setSelectedIds(ids);
              updateVisibleRows();
            }}
          />
        </Box>
        <Dialog open={lightboxOpen} onClose={() => setLightboxOpen(false)}>
          {currentImage && (
            <img
              src={currentImage.filepath}
              alt={currentImage.prompt_text}
              style={{
                maxWidth: '90vw',
                maxHeight: '90vh',
                objectFit: 'contain',
                cursor: 'pointer'
              }}
              onClick={() => setLightboxOpen(false)}
            />
          )}
        </Dialog>
      </Box>
    </ThemeProvider>
  );
}
