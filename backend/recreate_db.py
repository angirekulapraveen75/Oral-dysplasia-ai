import pymysql
import asyncio
import shutil
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine
from app.models import User, Slide, Patch, Annotation, Report

async def recreate_mysql_tables_force():
    print("=== OralDysplasia AI: Force Resetting XAMPP MySQL Database ===")
    
    db_name = "oraldysplasia"
    datadir = r"C:\xampp1\mysql\data"
    db_path = os.path.join(datadir, db_name)
    
    try:
        # 1. Connect to MySQL Server root
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            connect_timeout=3
        )
        cursor = conn.cursor()
        
        # 2. Try to drop database via SQL
        print("[1/4] Dropping database via SQL...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`;")
            conn.commit()
        except Exception as e:
            print(f"  [INFO] SQL Drop database warning: {e}")
            
        cursor.close()
        conn.close()
        
        # 3. Force clean the physical directory on Windows disk to clear orphaned .ibd tablespaces
        print("[2/4] Clearing orphaned .ibd tablespace files from XAMPP data directory...")
        if os.path.exists(db_path):
            try:
                shutil.rmtree(db_path)
                print("  [SUCCESS] Deleted physical database directory successfully.")
            except Exception as e:
                print(f"  [WARN] Failed to delete directory: {e}. Attempting file-by-file cleanup...")
                # Try file-by-file cleanup
                for filename in os.listdir(db_path):
                    file_p = os.path.join(db_path, filename)
                    try:
                        if os.path.isfile(file_p):
                            os.remove(file_p)
                        elif os.path.isdir(file_p):
                            shutil.rmtree(file_p)
                    except Exception as ex:
                        print(f"    Failed to remove {filename}: {ex}")
                try:
                    os.rmdir(db_path)
                    print("  [SUCCESS] Deleted physical database directory after file cleanup.")
                except Exception as ex:
                    print(f"    [ERROR] Could not remove database folder: {ex}")
        else:
            print("  [INFO] Database directory does not exist on disk.")

        # 4. Reconnect and recreate database
        print("[3/4] Creating fresh MySQL database...")
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE `{db_name}`;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        cursor.close()
        conn.close()
        print("  [SUCCESS] Database recreated in engine.")
        
        # 5. Run SQLAlchemy metadata sync
        print("[4/4] Syncing SQLAlchemy schemas to MySQL...")
        async with engine.begin() as conn_engine:
            await conn_engine.run_sync(Base.metadata.create_all)
        print("  [SUCCESS] All tables (users, slides, patches, annotations, reports) created successfully!")
        print("=== [FORCE RESET COMPLETED SUCCESSFULLY] ===")
        
    except Exception as e:
        print(f"  [ERROR] Force reset failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(recreate_mysql_tables_force())
