import logging

import docker
from docker.errors import NotFound

from resource.base import BaseResource


class DockerResource(BaseResource):
    def __init__(self):
        self.dc = self.docker_client = docker.from_env()
        self.logger = self._get_default_logger()

    @classmethod
    def _get_default_logger(cls):
        """获取默认的logger"""
        logging.basicConfig(format='%(asctime)s.%(msecs)d  %(module)s:%(process)s  %(levelname)s  %(message)s',
                            level=logging.INFO)
        logger = logging.getLogger('DockerResource')
        return logger

    def get_container(self, name=None, id=None):
        """获取指定容器"""
        try:
            container = self.dc.containers.get(name or id)
        except NotFound as e:
            self.logger.info(e)
            container = None
        return container

    def get_or_create_container(self, image_name, name=None, id=None, record_logging=False, **kwargs):
        """获取或创建容器"""

        # 获取容器
        container = self.get_container(name or id)

        # 不存在则创建容器
        if not container:
            container = self.dc.containers.run(image_name,
                                               name=name,
                                               detach=True,
                                               **kwargs)
        # 记录容器执行日志
        if record_logging:
            self.log_container(container)

        return container

    def container_to_json(self, container, detail=False):
        """容器对象序列化为json"""
        resp = {}
        if not container:
            return resp

        image_attrs = container.image.attrs
        resp = dict(id=container.id,
                    short_id=container.short_id,
                    repotags=image_attrs['RepoTags'],
                    labels=container.labels,
                    name=container.name,
                    ports=container.ports,
                    status=container.status,
                    create_time=image_attrs['Created'])

        if detail:
            attrs = container.attrs
            host_config = attrs['HostConfig']
            resp['total_memory'] = host_config['Memory']
        return resp

    def log_container(self, container):
        """打印容器执行日志"""
        logs = container.logs()
        self.logger.info(logs)
