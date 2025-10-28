# Unity Catalog Volumes Setup

This guide shows you how to create Unity Catalog Volumes for storing your application data on Databricks.

---

## 🎯 Why Use Unity Catalog Volumes?

✅ **Modern Best Practice** - Recommended by Databricks  
✅ **Better Performance** - Optimized for large files  
✅ **Fine-grained Access Control** - Per-volume permissions  
✅ **Data Governance** - Full lineage and auditing  
✅ **Cross-workspace Access** - Share data across workspaces  
✅ **POSIX-compliant** - Works like a regular file system  

---

## 📝 Step 1: Create Catalog and Schema (One-time Setup)

### Option A: Using Databricks UI

1. Go to **Data** in the left sidebar
2. Click **Create Catalog**
   - Name: `main` (or use existing)
3. Click on the catalog
4. Click **Create Schema**
   - Name: `default` (or use existing)

### Option B: Using SQL in a Notebook

```sql
-- Create catalog (if not exists)
CREATE CATALOG IF NOT EXISTS main;

-- Create schema (if not exists)
CREATE SCHEMA IF NOT EXISTS main.default;

-- Verify
SHOW CATALOGS;
SHOW SCHEMAS IN main;
```

---

## 📁 Step 2: Create Volumes for Application Data

Run this in a Databricks notebook:

```sql
-- Create volume for uploads (PDF, DOCX files)
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads
COMMENT 'Storage for uploaded documents (PDF, DOCX)';

-- Create volume for knowledge base (vector embeddings)
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_data
COMMENT 'Storage for vector embeddings and knowledge base';

-- Verify volumes were created
SHOW VOLUMES IN main.default;
```

---

## ✅ Step 3: Verify Volume Access

```python
# Run in a notebook cell
import os

# Check if volumes exist
uploads_path = "/Volumes/main/default/hackathon_chatbot_uploads"
data_path = "/Volumes/main/default/hackathon_chatbot_data"

if os.path.exists(uploads_path):
    print(f"✅ Uploads volume exists: {uploads_path}")
else:
    print(f"❌ Uploads volume not found: {uploads_path}")

if os.path.exists(data_path):
    print(f"✅ Data volume exists: {data_path}")
else:
    print(f"❌ Data volume not found: {data_path}")

# Test write access
try:
    test_file = f"{uploads_path}/test.txt"
    with open(test_file, 'w') as f:
        f.write("test")
    print("✅ Write access confirmed")
    os.remove(test_file)
except Exception as e:
    print(f"❌ Write access failed: {e}")
```

---

## 🔐 Step 4: Set Permissions (Optional)

```sql
-- Grant access to specific users/groups
GRANT READ, WRITE ON VOLUME main.default.hackathon_chatbot_uploads TO `user@domain.com`;
GRANT READ, WRITE ON VOLUME main.default.hackathon_chatbot_data TO `user@domain.com`;

-- Grant to all users (less secure, use for testing only)
GRANT READ, WRITE ON VOLUME main.default.hackathon_chatbot_uploads TO `account users`;
GRANT READ, WRITE ON VOLUME main.default.hackathon_chatbot_data TO `account users`;

-- Show current permissions
SHOW GRANTS ON VOLUME main.default.hackathon_chatbot_uploads;
SHOW GRANTS ON VOLUME main.default.hackathon_chatbot_data;
```

---

## 📊 Your Application Configuration

The code is **already updated** to use Unity Catalog Volumes!

### Storage Paths:
- **Uploads**: `/Volumes/main/default/hackathon_chatbot_uploads`
- **Data**: `/Volumes/main/default/hackathon_chatbot_data`

### Automatic Detection:
```python
# The code automatically uses volumes if available:
if os.path.exists("/Volumes"):
    # Use Unity Catalog Volumes (preferred)
    UPLOAD_DIR = "/Volumes/main/default/hackathon_chatbot_uploads"
    SIMPLE_DB_DIR = "/Volumes/main/default/hackathon_chatbot_data"
elif os.path.exists("/dbfs"):
    # Fallback to DBFS
    UPLOAD_DIR = "/dbfs/FileStore/hackathon-chatbot/uploads"
else:
    # Local development
    UPLOAD_DIR = "uploads"
```

---

## 🔄 Migrating from DBFS to Volumes (If Needed)

If you have existing data in DBFS:

```python
# Copy data from DBFS to Volumes
dbutils.fs.cp(
    "dbfs:/FileStore/hackathon-chatbot/uploads/",
    "/Volumes/main/default/hackathon_chatbot_uploads/",
    recurse=True
)

dbutils.fs.cp(
    "dbfs:/FileStore/hackathon-chatbot/simple_db/",
    "/Volumes/main/default/hackathon_chatbot_data/",
    recurse=True
)

print("✅ Data migrated to Unity Catalog Volumes")
```

---

## 📝 Managing Volumes

### List Files in Volume:
```python
# Using Python
import os
files = os.listdir("/Volumes/main/default/hackathon_chatbot_uploads")
print(files)

# Using dbutils
display(dbutils.fs.ls("/Volumes/main/default/hackathon_chatbot_uploads"))
```

### Delete Volume (if needed):
```sql
DROP VOLUME IF EXISTS main.default.hackathon_chatbot_uploads;
DROP VOLUME IF EXISTS main.default.hackathon_chatbot_data;
```

### Rename Volume:
```sql
ALTER VOLUME main.default.hackathon_chatbot_uploads 
RENAME TO main.default.my_new_volume_name;
```

### View Volume Details:
```sql
DESCRIBE VOLUME main.default.hackathon_chatbot_uploads;
```

---

## 🐛 Troubleshooting

### Issue: "Volume not found"

**Solution:**
```sql
-- Check if catalog exists
SHOW CATALOGS;

-- Check if schema exists
SHOW SCHEMAS IN main;

-- Check if volume exists
SHOW VOLUMES IN main.default;

-- Create if missing
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads;
```

### Issue: "Permission denied"

**Solution:**
```sql
-- Grant yourself permission
GRANT ALL PRIVILEGES ON VOLUME main.default.hackathon_chatbot_uploads TO `your-email@domain.com`;

-- Or ask workspace admin for access
```

### Issue: "Unity Catalog not enabled"

**Solution:**
- Unity Catalog must be enabled in your workspace
- Contact your Databricks admin
- Or use DBFS as fallback (code handles this automatically)

---

## 📊 Volume vs DBFS Comparison

| Feature | Unity Catalog Volumes | DBFS |
|---------|----------------------|------|
| **Performance** | ✅ Better | 🟡 Good |
| **Access Control** | ✅ Fine-grained | 🟡 Workspace-level |
| **Data Governance** | ✅ Full lineage | ❌ Limited |
| **Cross-workspace** | ✅ Yes | ❌ No |
| **Recommended** | ✅ **Yes** | 🟡 Legacy |

---

## ✅ Setup Complete!

Once volumes are created:
1. ✅ Run your notebook
2. ✅ Upload documents
3. ✅ Data stored in Unity Catalog Volumes
4. ✅ Full governance and auditability

---

## 🚀 Quick Setup Summary

```sql
-- 1. Create volumes
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads;
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_data;

-- 2. Verify
SHOW VOLUMES IN main.default;

-- 3. Test in Python
import os
print("Uploads:", os.path.exists("/Volumes/main/default/hackathon_chatbot_uploads"))
print("Data:", os.path.exists("/Volumes/main/default/hackathon_chatbot_data"))
```

**That's it!** Your application will automatically use Unity Catalog Volumes. 🎉

---

## 📚 Additional Resources

- [Unity Catalog Volumes Documentation](https://docs.databricks.com/en/connect/unity-catalog/volumes.html)
- [Managing Volumes](https://docs.databricks.com/en/sql/language-manual/sql-ref-syntax-ddl-create-volume.html)
- [Volume Permissions](https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/privileges.html)

---

**Next:** Return to your notebook and run it - volumes will be used automatically!

