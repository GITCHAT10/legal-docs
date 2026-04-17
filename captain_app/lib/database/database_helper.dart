import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'dmte_ledger.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE dispatch_logs (
        id TEXT PRIMARY KEY,
        vessel_id TEXT,
        captain_id TEXT,
        status TEXT,
        timestamp TEXT,
        synced INTEGER DEFAULT 0
      )
    ''');
  }

  Future<int> insertLog(Map<String, dynamic> row) async {
    Database db = await database;
    return await db.insert('dispatch_logs', row);
  }

  Future<List<Map<String, dynamic>>> getUnsyncedLogs() async {
    Database db = await database;
    return await db.query('dispatch_logs', where: 'synced = ?', whereArgs: [0]);
  }

  Future<int> markAsSynced(String id) async {
    Database db = await database;
    return await db.update(
      'dispatch_logs',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
