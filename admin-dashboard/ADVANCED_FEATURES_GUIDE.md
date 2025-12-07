# Advanced Features Integration Guide

## 🚀 Features Included

This module adds 12 advanced features to enhance your admin dashboard:

1. ✅ **Global Search** - Search across all entities with autocomplete
2. ✅ **Bulk Actions** - Select multiple items and perform batch operations
3. ✅ **Drag & Drop** - File uploads and item reordering
4. ✅ **Keyboard Shortcuts** - Quick actions with keyboard
5. ✅ **Infinite Scroll** - Auto-load more content
6. ✅ **Real-time Updates** - WebSocket integration for live data
7. ✅ **Toast Notifications** - Beautiful success/error messages
8. ✅ **Loading States** - Skeleton screens and spinners
9. ✅ **Confirmation Dialogs** - User-friendly confirmations
10. ✅ **Export Functionality** - Export to CSV/JSON/PDF
11. ✅ **Image Upload** - Drag & drop with preview
12. ✅ **Progress Indicators** - Visual feedback for operations

## 📦 Installation

### Step 1: Add CSS

Add to your HTML `<head>`:

```html
<link rel="stylesheet" href="css/advanced-features.css">
```

### Step 2: Add JavaScript

Add before closing `</body>`:

```html
<script src="js/advanced-features.js"></script>
```

## 🔧 Usage Examples

### Global Search

Add to your navbar:

```html
<div class="global-search-container">
    <i class="fas fa-search search-icon"></i>
    <input type="text" id="globalSearch" class="global-search-input" 
           placeholder="Search... (Ctrl+K or /)">
    <div id="searchDropdown" class="search-dropdown"></div>
</div>
```

**Keyboard Shortcuts:**
- `Ctrl+K` or `Cmd+K` - Open search
- `/` - Focus search
- `Enter` - Execute search

### Bulk Actions

Add checkboxes to your table:

```html
<!-- Select all checkbox -->
<input type="checkbox" id="selectAll">

<!-- Individual checkboxes -->
<input type="checkbox" class="item-checkbox" value="1">
<input type="checkbox" class="item-checkbox" value="2">

<!-- Bulk actions bar -->
<div id="bulkActionsBar" class="bulk-actions-bar">
    <span class="bulk-selected-count">
        <span id="selectedCount">0</span> items selected
    </span>
    <div class="bulk-actions-buttons">
        <button onclick="AdvancedFeatures.bulkActions.bulkDelete()">
            <i class="fas fa-trash"></i> Delete
        </button>
        <button onclick="AdvancedFeatures.bulkActions.bulkExport('csv')">
            <i class="fas fa-download"></i> Export
        </button>
    </div>
</div>
```

### Drag & Drop Upload

Add a drop zone:

```html
<div class="drop-zone">
    <div class="drop-zone-icon">
        <i class="fas fa-cloud-upload-alt"></i>
    </div>
    <div class="drop-zone-text">
        Drag & drop files here or click to upload
    </div>
</div>
```

### Toast Notifications

Show notifications:

```javascript
// Success
Utils.showToast('Operation successful!', 'success');

// Error
Utils.showToast('Something went wrong', 'error');

// Warning
Utils.showToast('Please review this', 'warning');

// Info
Utils.showToast('New update available', 'info');
```

### Keyboard Shortcuts

Built-in shortcuts:
- `Ctrl+K` - Open search
- `Ctrl+N` - New item
- `Ctrl+S` - Save
- `Esc` - Close modal
- `/` - Focus search

### Infinite Scroll

Enable on a container:

```javascript
const container = document.getElementById('itemsContainer');

AdvancedFeatures.infiniteScroll.init(container, async (page) => {
    const data = await API.get('/items/', { page });
    // Append data to container
    return data;
});
```

### Loading States

Skeleton screens:

```html
<div class="skeleton skeleton-title"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-card"></div>
```

Spinner:

```html
<div class="loading-spinner">
    <i class="fas fa-spinner fa-spin"></i>
    <p>Loading...</p>
</div>
```

### Confirmation Dialog

```javascript
if (confirm('Are you sure you want to delete this item?')) {
    // Proceed with deletion
}
```

### Real-time Updates (WebSocket)

Enable WebSocket connection:

```javascript
// Uncomment in advanced-features.js
AdvancedFeatures.realtime.init();
```

Backend WebSocket URL: `ws://localhost:8000/ws/admin/`

Message format:
```json
{
    "type": "notification",
    "message": "New user registered",
    "level": "info"
}
```

## 🎨 Customization

### Change Toast Position

Edit CSS:

```css
.toast-container {
    top: 20px;    /* Change to bottom: 20px for bottom */
    right: 20px;  /* Change to left: 20px for left */
}
```

### Customize Progress Bar Colors

```css
.progress-fill {
    background: linear-gradient(90deg, #your-color-1, #your-color-2);
}
```

### Adjust Animation Speed

```css
.toast {
    animation: slideIn 0.5s ease; /* Change 0.3s to 0.5s */
}
```

## 📊 API Integration

### Search Endpoint

```python
# Django view
@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '')
    results = []
    
    # Search users
    users = User.objects.filter(username__icontains=query)[:5]
    results.extend([{
        'id': u.id,
        'title': u.username,
        'type': 'user'
    } for u in users])
    
    # Search posts
    posts = Post.objects.filter(caption__icontains=query)[:5]
    results.extend([{
        'id': p.id,
        'title': p.caption[:50],
        'type': 'post'
    } for p in posts])
    
    return Response(results)
```

### Export Endpoint

```python
@api_view(['POST'])
def export_data(request):
    ids = request.data.get('ids', [])
    format = request.data.get('format', 'csv')
    
    items = Item.objects.filter(id__in=ids)
    
    if format == 'csv':
        # Generate CSV
        pass
    elif format == 'json':
        # Generate JSON
        pass
    
    return Response(data)
```

### Upload Endpoint

```python
@api_view(['POST'])
def upload_file(request):
    file = request.FILES.get('file')
    
    # Save file
    instance = FileUpload.objects.create(file=file)
    
    return Response({
        'url': instance.file.url,
        'filename': file.name
    })
```

## 🔐 Security Considerations

1. **File Upload Validation**
   - Check file types
   - Limit file sizes
   - Scan for malware

2. **Bulk Actions**
   - Verify permissions
   - Rate limiting
   - Transaction safety

3. **WebSocket**
   - Authenticate connections
   - Validate messages
   - Rate limiting

## 🐛 Troubleshooting

### Search not working?
- Check API endpoint is correct
- Verify CORS settings
- Check browser console for errors

### Bulk actions not showing?
- Ensure checkboxes have correct classes
- Check `bulkActionsBar` element exists
- Verify JavaScript is loaded

### Drag & drop not working?
- Check browser supports drag & drop API
- Verify drop zone has correct class
- Check file upload endpoint

### WebSocket not connecting?
- Verify WebSocket URL is correct
- Check Django Channels is installed
- Ensure WebSocket route is configured

## 📱 Mobile Support

All features are mobile-responsive:
- Touch-friendly drag & drop
- Mobile-optimized search
- Responsive bulk actions bar
- Touch-friendly toast notifications

## ⚡ Performance Tips

1. **Debounce search** - Already implemented (300ms)
2. **Lazy load images** - Use `loading="lazy"`
3. **Limit results** - Show max 10 search results
4. **Throttle scroll** - Infinite scroll has built-in throttling

## 🎯 Best Practices

1. **Always show feedback** - Use toasts for all actions
2. **Confirm destructive actions** - Use confirmation dialogs
3. **Show progress** - Use progress bars for long operations
4. **Handle errors gracefully** - Show user-friendly error messages
5. **Keyboard accessibility** - Support keyboard navigation

## 📚 Additional Resources

- [MDN Drag & Drop API](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Intersection Observer](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)

## 🆘 Support

If you encounter issues:
1. Check browser console for errors
2. Verify all files are loaded
3. Check API endpoints are working
4. Review network tab for failed requests
