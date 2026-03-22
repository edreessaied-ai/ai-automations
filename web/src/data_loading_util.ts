/*
    This file contains utility functions for loading data from the server or backend.
*/

async function fetchWithTimeout(url: string, timeoutMs: number = 10000): Promise<Response> {
    /*
    Utility function to fetch with a timeout. If the request takes longer than the specified timeout, it will be aborted.
    */
    // Create an AbortController to handle the timeout
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    // Perform the fetch request with the abort signal
    const response = await fetch(url, { signal: controller.signal });

    clearTimeout(id);
    return response;
}

export { fetchWithTimeout };