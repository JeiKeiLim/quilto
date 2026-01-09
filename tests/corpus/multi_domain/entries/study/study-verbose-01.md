Today marked week 3 of my deep dive into data structures and algorithms. I've committed to spending at least 2 hours every day preparing for technical interviews at big tech companies, and today was particularly productive.

Started the morning with a review of binary search trees. I thought I understood them from my CS degree, but implementing a balanced AVL tree from scratch revealed some gaps. The rotation operations - left rotation, right rotation, left-right, right-left - are tricky to get right. Spent about 45 minutes just on the rebalancing logic after insertions. Drew out the tree transformations on paper which helped immensely.

Then I moved on to LeetCode problems. Did 3 medium-difficulty problems:
1. "Validate Binary Search Tree" - Got it on second attempt. First try I forgot about the global min/max bounds approach and tried doing it with just parent comparisons (which fails for grandparent violations).
2. "Lowest Common Ancestor of BST" - This one clicked immediately once I recognized the BST property means we can use value comparisons. O(h) time, very elegant.
3. "Kth Smallest Element in BST" - Used in-order traversal with early termination. Could optimize with augmented tree storing subtree sizes but that felt like overkill.

Afternoon session was system design focused. Read through "Designing Data-Intensive Applications" chapter on replication. Single-leader, multi-leader, and leaderless replication strategies. The trade-offs between consistency and availability really depend on use case. Social media can tolerate eventual consistency; banking cannot.

Finished the day with a mock interview on Pramp. My partner was preparing for Google and we practiced explaining our thought process out loud. Feedback was that I jump to coding too fast without fully clarifying requirements. Need to work on asking more clarifying questions upfront.

Tomorrow's plan: Red-black trees and 3 more LeetCode problems. Also need to review the CAP theorem more deeply - I can recite it but don't think I truly understand the nuances.

Total study time today: 4 hours 20 minutes. Feeling confident but there's still so much to learn.
