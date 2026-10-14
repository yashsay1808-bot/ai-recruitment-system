// Node needs file extensions on relative imports; Vite does not. This hook lets the tests import the
// application modules exactly as the app does ("./interviewQuestions") without changing them.
export async function resolve(specifier, context, nextResolve) {
  if ((specifier.startsWith("./") || specifier.startsWith("../")) && !/\.[a-z]+$/i.test(specifier)) {
    try {
      return await nextResolve(`${specifier}.js`, context);
    } catch {
      /* fall through to the default resolver */
    }
  }
  return nextResolve(specifier, context);
}
