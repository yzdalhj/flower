from typing import Dict, List, Set

import networkx as nx

from app.services.profile.models import UserProfile


class RelationshipGraphService:
    """
    关系图分析服务
    使用NetworkX构建和分析用户关系网络
    """

    def __init__(self):
        # 关系图: 用户 -> 实体/人物关系
        self.graph = nx.DiGraph()

    def build_user_entity_graph(self, user_id: str, profile: UserProfile):
        """
        构建用户-实体关系图
        """
        # 添加用户节点
        self.graph.add_node(
            user_id,
            type="user",
            intimacy=profile.relationship.intimacy,
            trust=profile.relationship.trust,
        )

        # 添加实体节点和关系
        entities = profile.extracted_entities

        # 人物关系
        for person in entities.get("PERSON", []):
            self.graph.add_node(person, type="person")
            self.graph.add_edge(user_id, person, relation="knows", weight=0.5)

        # 地点关系
        for location in entities.get("GPE", []):
            self.graph.add_node(location, type="location")
            self.graph.add_edge(user_id, location, relation="located_at", weight=0.3)

        # 组织关系
        for org in entities.get("ORG", []):
            self.graph.add_node(org, type="organization")
            self.graph.add_edge(user_id, org, relation="works_at", weight=0.4)

        # 事件关系
        for event in entities.get("EVENT", []):
            self.graph.add_node(event, type="event")
            self.graph.add_edge(user_id, event, relation="participated", weight=0.6)

        # 兴趣关系
        for like in profile.preferences.get("likes", []):
            self.graph.add_node(like, type="interest")
            self.graph.add_edge(user_id, like, relation="likes", weight=0.7)

        # 厌恶关系
        for dislike in profile.preferences.get("dislikes", []):
            self.graph.add_node(dislike, type="interest")
            self.graph.add_edge(user_id, dislike, relation="dislikes", weight=0.7)

    def find_common_interests(self, user_id1: str, user_id2: str) -> List[str]:
        """
        发现两个用户的共同兴趣
        用于群体关系分析
        """
        if user_id1 not in self.graph or user_id2 not in self.graph:
            return []

        # 获取共同邻居（实体）
        neighbors1 = set(self.graph.neighbors(user_id1))
        neighbors2 = set(self.graph.neighbors(user_id2))
        common = neighbors1 & neighbors2

        # 过滤出兴趣相关实体
        interests = []
        for node in common:
            node_type = self.graph.nodes[node].get("type")
            if node_type in ["interest", "hobby", "topic"]:
                interests.append(node)

        return interests

    def calculate_centrality(self, user_id: str) -> Dict[str, float]:
        """
        计算用户在关系网络中的中心性
        """
        if user_id not in self.graph:
            return {}

        return {
            "degree": nx.degree_centrality(self.graph).get(user_id, 0),
            "betweenness": nx.betweenness_centrality(self.graph).get(user_id, 0),
            "closeness": nx.closeness_centrality(self.graph).get(user_id, 0),
        }

    def detect_communities(self) -> List[Set[str]]:
        """
        检测关系社区/圈子
        使用Louvain算法检测社区
        """
        # 使用Louvain算法检测社区
        undirected = self.graph.to_undirected()
        communities = nx.community.louvain_communities(undirected, resolution=1.0)

        # 只返回包含用户的社区
        user_communities = []
        for community in communities:
            has_user = any(self.graph.nodes[node].get("type") == "user" for node in community)
            if has_user:
                user_communities.append(community)

        return user_communities

    def recommend_topics(self, user_id: str, top_k: int = 5) -> List[str]:
        """
        基于关系图推荐用户可能感兴趣的话题
        """
        if user_id not in self.graph:
            return []

        # 获取用户已有的兴趣
        existing_interests = set()
        for neighbor in self.graph.neighbors(user_id):
            if self.graph.nodes[neighbor].get("type") == "interest":
                existing_interests.add(neighbor)

        # 寻找与用户兴趣相似的节点，使用PageRank
        personalization = {
            node: 1.0 if node in existing_interests else 0.0 for node in self.graph.nodes()
        }
        pagerank = nx.pagerank(self.graph, personalization=personalization)

        # 排序并过滤已有的兴趣
        recommendations = []
        for node, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
            if node not in existing_interests and self.graph.nodes[node].get("type") == "interest":
                recommendations.append(node)
                if len(recommendations) >= top_k:
                    break

        return recommendations

    def get_social_distance(self, user_id1: str, user_id2: str) -> int:
        """
        计算两个用户之间的社交距离（最短路径长度）
        """
        if user_id1 not in self.graph or user_id2 not in self.graph:
            return -1

        try:
            return nx.shortest_path_length(self.graph, user_id1, user_id2)
        except nx.NetworkXNoPath:
            return -1

    def export_graph(self, path: str = "relationship_graph.gexf"):
        """
        导出关系图为GEXF格式，用于可视化
        """
        nx.write_gexf(self.graph, path)
