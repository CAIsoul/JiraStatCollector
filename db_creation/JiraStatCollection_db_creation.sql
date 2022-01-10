-- 1. Create [JiraStatCollection] database --
DECLARE @dbname NVARCHAR(128)
SET @dbname = N'JiraStatCollection'

IF NOT EXISTS (
    SELECT [name] FROM [master].[sys].[databases]
    WHERE ('[' + [name] + ']' = @dbname OR [name] = @dbname)
)
BEGIN

    CREATE DATABASE [JiraStatCollection]

END

GO

-- Create requried data tables --

USE [JiraStatCollection]

-- 2. Create [ServeType] data table --
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES 
	WHERE [TABLE_CATALOG] = 'JiraStatCollection' AND [TABLE_NAME] = 'ServeType'
)
BEGIN

	CREATE TABLE [ServeType]
	(
		[Id] SMALLINT NOT NULL IDENTITY,
		[Type] NVARCHAR(20) NOT NULL,
		CONSTRAINT PK_ServeType PRIMARY KEY NONCLUSTERED (Id),
	)

	INSERT INTO [ServeType] (Type)
	VALUES
	('Sprint'),
	('Board')
END

GO

-- 3. Create [DataSnapshot] data table --
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES 
	WHERE [TABLE_CATALOG] = 'JiraStatCollection' AND [TABLE_NAME] = 'DataSnapshot'
)
BEGIN

	CREATE TABLE [DataSnapshot]
	(
		[Id] INT NOT NULL IDENTITY,
		[ServeType] SMALLINT NOT NULL,
		[ServeId] INT NOT NULL,
		[SnapshotTime] DATETIME NOT NULL,
		CONSTRAINT PK_DataSnapshot PRIMARY KEY NONCLUSTERED (Id),
		CONSTRAINT FK_DataSnapshot_ServeType FOREIGN KEY (ServeType) 
		REFERENCES [ServeType] (Id) ON DELETE CASCADE ON UPDATE CASCADE
	)

END

GO


-- 4. Create [JiraIssue] data table --
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES 
	WHERE [TABLE_CATALOG] = 'JiraStatCollection' AND [TABLE_NAME] = 'JiraIssue'
)
BEGIN

	CREATE TABLE [JiraIssue]
	(
		[Id] INT NOT NULL IDENTITY,
		[SnapshotId] INT NOT NULL,
		[ObjectId] INT NOT NULL,
		[Key] NVARCHAR(20) NOT NULL,
		[Type] NVARCHAR(20) NOT NULL,
		[Status] NVARCHAR(50) NOT NULL,
		[ResolutionDate] DATETIME NULL,
		[StoryPoint] DECIMAL NULL,
		[ParentIssueId] INT NULL,
		CONSTRAINT PK_JiraIssue PRIMARY KEY NONCLUSTERED (Id),
		CONSTRAINT FK_JiraIssue_DataSnapshot FOREIGN KEY (SnapshotId)
		REFERENCES [DataSnapshot] (Id) ON DELETE CASCADE ON UPDATE CASCADE
	)

END

GO


-- 5. Create [WorkLog] data table --
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES 
	WHERE [TABLE_CATALOG] = 'JiraStatCollection' AND [TABLE_NAME] = 'WorkLog'
)
BEGIN

	CREATE TABLE [WorkLog]
	(
		[Id] INT NOT NULL IDENTITY,
		[SnapshotId] INT NOT NULL,
		[TimeInSecond] INT NOT NULL,
		[IssueId] INT NOT NULL,
		[AuthorName] NVARCHAR(50) NOT NULL,
		[CreateDate] DATETIME NOT NULL,
		[UpdateDate] NVARCHAR(20) NOT NULL,
		CONSTRAINT PK_WorkLog PRIMARY KEY NONCLUSTERED (Id),
		CONSTRAINT FK_WorkLog_DataSnapshot FOREIGN KEY (SnapshotId)
		REFERENCES [DataSnapshot] (Id) ON DELETE CASCADE ON UPDATE CASCADE
	)

END

GO