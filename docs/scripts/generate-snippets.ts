const fs = require('node:fs');
const path = require('node:path');
const { glob } = require('glob');

async function generateSnippets() {
  const rootDir = path.resolve(__dirname, '../../');
  const snippetsDir = path.resolve(__dirname, '../snippets');

  // Find all SDK example files (not directories)
  const examplePaths = await glob('examples/**/*.{py,go,ts}', {
    cwd: rootDir,
    ignore: [
      '**/node_modules/**',
      '**/*.cpython-*',
      '**/__pycache__/**'
    ],
    nodir: true // Only match files, not directories
  });

  // Ensure snippets directory exists
  await fs.promises.mkdir(snippetsDir, { recursive: true });

  // Process each example file
  for (const filepath of examplePaths) {
    const content = await fs.promises.readFile(path.join(rootDir, filepath), 'utf-8');
    const ext = path.extname(filepath);
    const filename = path.basename(filepath, ext);
    const sdkName = filepath.split('/')[1]; // e.g., 'node', 'python'

    const snippetFilename = `${sdkName}-${filename}.mdx`;

    // Determine the language for syntax highlighting based on file extension
    const language = ext.slice(1); // Remove the dot from extension

    // Wrap content in code block with syntax highlighting
    const mdxContent = `\`\`\`${language}\n${content}\n\`\`\``;

    // Write the snippet file
    await fs.promises.writeFile(
      path.join(snippetsDir, snippetFilename),
      mdxContent
    );
  }

  console.log(`Generated ${examplePaths.length} snippets in ./snippets`);
}

// Run the script
generateSnippets().catch(console.error);
