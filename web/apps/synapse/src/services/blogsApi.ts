/**
 * Blogs API Service
 */

// Helper function to make raw HTTP calls
const fetchApi = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
};

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  subtitle: string;
  content: string;
  cover_image: string | null;
  author_name: string;
  created_at: string;
  published_at: string | null;
  is_published: boolean;
  tags: string[];
}

export const blogsApi = {
  /**
   * Get all published blog posts
   */
  getBlogPosts: async (): Promise<BlogPost[]> => {
    return fetchApi<BlogPost[]>("/api/blogs/");
  },

  /**
   * Get a single blog post by slug
   */
  getBlogPostBySlug: async (slug: string): Promise<BlogPost> => {
    return fetchApi<BlogPost>(`/api/blogs/${slug}/`);
  },
};
